# Memory Full & Evictions

## Overview

One of the most common production incidents in Redis is running out of memory. Since Redis is an **in-memory database**, every key, value, expiration metadata, and internal data structure consumes RAM.

When Redis reaches its configured memory limit, it cannot continue storing data normally. Depending on the configured eviction policy, Redis may:

- Reject write operations
- Evict existing keys
- Delete expired data
- Experience latency spikes
- Cause application failures

Understanding memory management and eviction policies is essential for building reliable, scalable Redis deployments.

---

# How Redis Uses Memory

Redis stores data primarily in RAM.

```
                +------------------------+
                |       Redis Server     |
                +------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
      Keys            Values          Metadata
         |                 |                 |
         +-----------------+-----------------+
                           |
                      Physical Memory
```

Memory is consumed by:

- Keys
- Values
- Expiration metadata
- Replication buffers
- Client buffers
- Lua scripts
- Internal allocator overhead

---

# Symptoms

Typical application errors include:

```text
OOM command not allowed when used memory > 'maxmemory'
```

```text
MISCONF Redis is configured to save RDB snapshots...
```

Application logs may contain:

```text
RedisError: OOM command not allowed
```

Users may observe:

- Failed writes
- Slow response times
- Missing cache entries
- Increased cache misses
- High CPU usage

---

# Memory Management Workflow

```
Application

        │

        ▼

Write Request

        │

        ▼

Memory Available?

        │

 ┌──────┴───────┐

 │              │

Yes             No

 │              │

Store Data   Eviction Policy

                 │

        ┌────────┴─────────┐

        │                  │

 Evict Keys         Reject Writes
```

---

# Checking Memory Usage

Use

```bash
redis-cli INFO memory
```

Example

```text
used_memory:512000000

used_memory_human:488M

maxmemory:536870912

maxmemory_human:512M
```

Important fields:

- used_memory
- maxmemory
- mem_fragmentation_ratio
- allocator statistics

---

# Memory Statistics

Useful commands

```bash
INFO memory
```

```bash
MEMORY STATS
```

```bash
MEMORY USAGE user:100
```

```bash
MEMORY DOCTOR
```

These commands help identify memory pressure and inefficient usage.

---

# maxmemory Configuration

Example

```conf
maxmemory 2gb
```

Once Redis reaches this limit, eviction behavior depends on the configured policy.

---

# Eviction Policies

Check

```bash
CONFIG GET maxmemory-policy
```

Example

```text
allkeys-lru
```

Redis supports several eviction policies.

| Policy | Description |
|---------|-------------|
| noeviction | Reject new writes |
| allkeys-lru | Remove least recently used key |
| volatile-lru | Remove least recently used expiring key |
| allkeys-random | Remove random key |
| volatile-random | Remove random expiring key |
| volatile-ttl | Remove key closest to expiration |
| allkeys-lfu | Remove least frequently used key |
| volatile-lfu | Remove least frequently used expiring key |

---

# noeviction

```
Memory Full

↓

Reject Writes

↓

OOM Error
```

Best suited for:

- Financial systems
- Persistent data
- Critical state

---

# allkeys-lru

```
Memory Full

↓

Least Recently Used Key

↓

Evicted

↓

Store New Key
```

Ideal for cache workloads.

---

# allkeys-lfu

```
Memory Full

↓

Least Frequently Used

↓

Evicted
```

Better for workloads where frequently accessed keys should remain cached.

---

# volatile-lru

Only keys with expiration times are eligible.

```
Persistent Keys

↓

Never Evicted
```

Useful when persistent and cache data coexist.

---

# Eviction Metrics

Monitor

```bash
INFO stats
```

Important metrics

```text
evicted_keys

expired_keys
```

Large increases in

```
evicted_keys
```

usually indicate memory pressure.

---

# Fragmentation

Redis may use significantly more RAM than expected.

Example

```bash
INFO memory
```

```
mem_fragmentation_ratio
```

Typical values

| Ratio | Meaning |
|--------|----------|
| 1.0 | Excellent |
| 1.1–1.5 | Normal |
| >1.5 | Investigate |
| >2.0 | High fragmentation |

---

# Large Keys

A single large key can consume substantial memory.

Find large keys

```bash
redis-cli --bigkeys
```

Example

```
Largest hash

Largest list

Largest string
```

---

# Hot Keys

Hot keys consume CPU and remain resident in memory.

Example

```
Popular Product

↓

Millions of Reads
```

Mitigation

- Sharding
- Replication
- Local caching

---

# Memory Leak Investigation

Redis itself rarely leaks memory.

Common causes include:

- Applications never deleting keys
- Missing TTLs
- Growing lists
- Infinite streams
- Large hashes

Monitor key growth over time.

---

# Missing TTL

Bad

```
SET session:100 data
```

Good

```
SETEX session:100 3600 data
```

Always expire cache entries unless persistence is required.

---

# Lazy Expiration

Expired keys are removed

- During access
- Periodically by Redis

Memory may not be reclaimed immediately.

---

# Active Expiration

Redis continuously scans expired keys.

```
Expired Key

↓

Background Cleanup

↓

Memory Released
```

---

# Replication Buffers

Replication consumes memory.

```
Primary

↓

Replication Buffer

↓

Replica
```

Large write bursts increase buffer size.

Monitor

```bash
INFO replication
```

---

# Client Buffers

Slow clients accumulate buffers.

Check

```bash
CLIENT LIST
```

Look for

```
omem=
```

Large output buffers may indicate slow consumers.

---

# Persistence Overhead

During

- BGSAVE
- BGREWRITEAOF

Redis temporarily uses additional memory.

```
Parent Process

↓

Fork

↓

Child Process

↓

Snapshot
```

Plan sufficient free RAM before running persistence operations.

---

# Docker Memory Limits

Container limits may be lower than Redis configuration.

Example

```
Docker Limit

↓

1 GB
```

Redis

```
maxmemory

↓

2 GB
```

Result

```
OOM Killer
```

Ensure container and Redis limits are aligned.

---

# Kubernetes Memory Limits

```
Pod

↓

Memory Limit

↓

Exceeded

↓

OOMKilled
```

Verify

```bash
kubectl describe pod redis
```

Monitor

```bash
kubectl top pod
```

---

# AWS ElastiCache

Monitor CloudWatch metrics

- DatabaseMemoryUsagePercentage
- FreeableMemory
- Evictions
- SwapUsage

Configure alarms before memory reaches critical levels.

---

# Capacity Planning

Estimate memory requirements

```
Average Key Size

×

Number of Keys

+

Overhead

+

Replication

+

Fragmentation

=

Required RAM
```

Always reserve additional capacity for maintenance operations.

---

# Diagnostic Workflow

```
OOM Error

        │

        ▼

Check INFO memory

        │

        ▼

Memory Near Limit?

        │

 ┌──────┴───────┐

 │              │

Yes             No

 │              │

Check Policy   Investigate Other Issues

 │

 ▼

Review Evictions

 │

 ▼

Check Large Keys

 │

 ▼

Optimize Memory

 │

 ▼

Monitor Continuously
```

---

# Common Mistakes

## No Memory Limit

Unlimited memory may allow Redis to consume all available RAM, causing the operating system to terminate the process.

---

## Wrong Eviction Policy

Using

```
noeviction
```

for a cache workload often results in unnecessary application failures.

---

## Missing TTLs

Cache entries without expiration continue consuming memory indefinitely.

---

## Ignoring Fragmentation

Low logical memory usage does not guarantee low physical memory consumption.

---

## Oversized Keys

Large hashes, lists, or strings can quickly exhaust available memory.

---

# Best Practices

- Configure `maxmemory` for every production deployment.
- Choose an eviction policy appropriate for the workload.
- Assign TTLs to cache entries whenever possible.
- Monitor memory utilization continuously.
- Investigate increasing eviction counts promptly.
- Identify and optimize large keys.
- Leave sufficient free memory for persistence operations.
- Regularly review fragmentation and allocator metrics.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Memory Limit | Configure `maxmemory` appropriately |
| Eviction Policy | Match workload characteristics |
| Large Keys | Split oversized data structures |
| TTL | Expire cache entries automatically |
| Fragmentation | Monitor `mem_fragmentation_ratio` |
| Replication | Account for replication buffers |

---

# Production Considerations

For production deployments:

- Configure alerts when memory usage exceeds 80–85%.
- Alert on sudden increases in `evicted_keys`.
- Regularly analyze key distribution using `--bigkeys`.
- Reserve additional RAM for background persistence.
- Align container memory limits with Redis configuration.
- Test eviction behavior in staging before production rollout.
- Document memory capacity planning and growth projections.

---

# Summary

Memory exhaustion is a common Redis production issue that directly impacts application availability and performance. By configuring appropriate memory limits, selecting the correct eviction policy, monitoring memory metrics, and proactively managing large keys and TTLs, engineers can prevent most out-of-memory incidents and maintain stable Redis deployments.

---

# Key Takeaways

- Redis stores all active data in memory, making RAM management critical.
- Configure `maxmemory` and an appropriate eviction policy for every deployment.
- Monitor memory usage, fragmentation, and eviction metrics continuously.
- Use TTLs to prevent unnecessary memory growth.
- Investigate large keys and hot keys before they become production issues.
- Account for replication and persistence overhead when sizing infrastructure.
- Align container memory limits with Redis configuration.
- Proactive monitoring and capacity planning are the best defenses against memory-related outages.