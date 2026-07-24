# High Latency

## Overview

Redis is designed to serve most operations in **sub-millisecond** time. When applications suddenly experience high latency, it usually indicates an underlying infrastructure, networking, memory, persistence, or workload problem rather than Redis itself.

Typical symptoms include:

```text
Request timeout
```

```text
Redis command took 500 ms
```

```text
Socket timeout
```

```text
Timeout connecting to Redis
```

Applications may experience:

- Slow API responses
- Increased request latency
- Connection timeouts
- Queue backlogs
- Cache misses
- Cascading failures

High latency should always be investigated immediately because it often affects every application using Redis.

---

# Typical Latency Targets

| Operation | Expected Latency |
|------------|-----------------|
| GET | < 1 ms |
| SET | < 1 ms |
| INCR | < 1 ms |
| HGET | < 1 ms |
| Network RTT (same DC) | < 1 ms |
| Cross Region | 20–150 ms |

Any sustained latency above these values should be investigated.

---

# Troubleshooting Workflow

```
Application Slow

        │

        ▼

Measure Latency

        │

        ▼

Redis Slow?

        │

 ┌──────┴────────┐

 │               │

Yes              No

 │               │

Investigate     Application

Redis           Issue

 │

 ▼

CPU

Memory

Disk

Network

Persistence

Slow Commands

Client Issues

```

---

# Step 1 — Verify Redis Health

Run

```bash
redis-cli INFO
```

Check

- uptime
- connected_clients
- used_memory
- instantaneous_ops_per_sec

If Redis appears healthy, investigate networking or the application.

---

# Step 2 — Measure Network Latency

Test connectivity

```bash
ping redis-server
```

Measure TCP latency

```bash
redis-cli --latency
```

Example

```text
min: 0 ms

max: 1 ms

avg: 0.32 ms
```

High average latency usually indicates infrastructure problems.

---

# Step 3 — Use LATENCY Command

Redis provides built-in latency monitoring.

Enable

```bash
CONFIG SET latency-monitor-threshold 100
```

View events

```bash
LATENCY LATEST
```

View graph

```bash
LATENCY GRAPH command
```

History

```bash
LATENCY HISTORY command
```

---

# Step 4 — Check Slow Log

View slow operations

```bash
SLOWLOG GET
```

Example

```text
Command

Duration

Timestamp
```

Large entries indicate expensive commands.

---

# Common Causes

| Cause | Symptoms |
|--------|----------|
| Slow commands | High CPU |
| Large keys | Long execution time |
| Persistence | Temporary latency |
| Memory pressure | Evictions |
| Network | High RTT |
| Client overload | Connection delays |
| Replication | Replica lag |
| CPU saturation | Slow responses |

---

# Slow Commands

Expensive operations include

```
KEYS *

SMEMBERS

HGETALL

LRANGE (large)

ZRANGE (large)

SCAN with huge COUNT
```

Prefer incremental operations.

---

# Large Keys

Example

```
100 MB Hash

↓

HGETALL

↓

High Latency
```

Find them

```bash
redis-cli --bigkeys
```

---

# CPU Saturation

Check

```bash
top
```

or

```bash
htop
```

High CPU usage can delay command execution.

Monitor

```bash
INFO cpu
```

---

# Memory Pressure

Inspect

```bash
INFO memory
```

Look for

- used_memory
- fragmentation
- evictions

Memory pressure often increases latency.

---

# Persistence Impact

During

```
BGSAVE

BGREWRITEAOF
```

Redis forks a child process.

```
Redis

↓

Fork

↓

Snapshot

↓

Temporary Latency
```

Large datasets increase fork time.

---

# Disk Performance

Persistence depends on disk throughput.

Monitor

```bash
iostat
```

Watch for

- High disk utilization
- Slow writes
- Queue depth

---

# Network Congestion

Architecture

```
Application

↓

Switch

↓

Firewall

↓

Redis
```

Latency can occur anywhere along the path.

Measure

```bash
traceroute
```

or

```bash
mtr
```

---

# DNS Resolution

Applications repeatedly resolving hostnames may experience delays.

Prefer connection pools and persistent connections.

---

# Connection Pool Exhaustion

Poor

```
Request

↓

Open Connection

↓

Close Connection
```

Better

```
Connection Pool

↓

Reuse Connections
```

Pooling significantly reduces latency.

---

# Replication

Heavy replication traffic may increase latency.

Inspect

```bash
INFO replication
```

Monitor

- replica lag
- replication backlog
- network utilization

---

# Lua Scripts

Long-running scripts block Redis.

Example

```
Lua Script

↓

Redis Busy

↓

Other Clients Wait
```

Keep scripts short.

---

# Blocking Commands

Commands such as

```
BLPOP

BRPOP

XREAD BLOCK
```

are expected to wait.

Do not confuse blocking behavior with latency issues.

---

# Hot Keys

Millions of requests hitting a single key

```
Clients

↓↓↓↓↓

Hot Key

↓

CPU Spike
```

Mitigation

- Sharding
- Replication
- Local caching

---

# Client Buffers

Inspect

```bash
CLIENT LIST
```

Large

```
omem=
```

values indicate slow clients.

---

# Docker

Verify

```bash
docker stats
```

Look for

- CPU throttling
- Memory limits
- Network bandwidth

---

# Kubernetes

Check

```bash
kubectl top pod
```

Inspect

- CPU throttling
- Memory pressure
- Network policies

---

# AWS ElastiCache

Monitor CloudWatch

- EngineCPUUtilization
- CurrConnections
- NetworkBytesIn
- NetworkBytesOut
- ReplicationLag
- CacheHits
- CacheMisses

---

# Latency Monitoring Workflow

```
High Latency

        │

        ▼

Measure RTT

        │

        ▼

Redis Slow?

        │

 ┌──────┴────────┐

 │               │

Yes              No

 │               │

Slow Log      Network

 │

 ▼

Large Keys

 │

 ▼

CPU

 │

 ▼

Memory

 │

 ▼

Persistence

 │

 ▼

Resolution
```

---

# Useful Commands

```bash
redis-cli INFO
```

```bash
redis-cli --latency
```

```bash
LATENCY LATEST
```

```bash
LATENCY GRAPH command
```

```bash
SLOWLOG GET
```

```bash
CLIENT LIST
```

```bash
INFO cpu
```

```bash
INFO memory
```

---

# Common Mistakes

## Using KEYS in Production

```
KEYS *
```

blocks Redis while scanning the database.

Use

```
SCAN
```

instead.

---

## No Connection Pool

Opening a TCP connection for every request significantly increases latency.

---

## Large Data Structures

Very large hashes, lists, or sets increase command execution time.

---

## Ignoring Slow Log

The Slow Log often identifies the exact command responsible for latency.

---

## Cross-Region Access

Applications accessing Redis across regions introduce unavoidable network latency.

Deploy Redis close to the application.

---

# Best Practices

- Keep Redis and applications in the same availability zone whenever possible.
- Monitor latency continuously using Redis and infrastructure metrics.
- Review the Slow Log regularly.
- Replace blocking operations with incremental alternatives.
- Use connection pooling.
- Avoid oversized keys.
- Monitor CPU, memory, and replication.
- Benchmark changes before deploying to production.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Network | Keep Redis close to applications |
| Commands | Avoid blocking operations |
| Connection Pool | Reuse TCP connections |
| Monitoring | Enable latency monitoring |
| CPU | Watch utilization continuously |
| Persistence | Schedule during off-peak hours |

---

# Production Considerations

For production environments:

- Configure alerts on latency spikes.
- Track P95 and P99 Redis latency in observability dashboards.
- Review the Slow Log as part of regular maintenance.
- Load test Redis before major releases.
- Scale vertically or horizontally before CPU saturation occurs.
- Keep infrastructure, networking, and Redis metrics correlated during incident investigations.
- Document latency baselines for each environment.

---

# Summary

Redis is capable of extremely low response times, so sustained latency is almost always a sign of an underlying issue. By systematically examining network performance, slow commands, CPU utilization, memory pressure, persistence operations, and client behavior, engineers can quickly identify the root cause and restore optimal performance.

---

# Key Takeaways

- Redis operations should typically complete in less than one millisecond.
- Use `LATENCY` commands and `SLOWLOG` to identify bottlenecks.
- Avoid blocking commands and oversized keys.
- Monitor CPU, memory, replication, and network health together.
- Use connection pooling and deploy Redis close to applications.
- Track latency trends continuously to detect problems before they impact users.
- Build runbooks for recurring latency scenarios to reduce incident response time.