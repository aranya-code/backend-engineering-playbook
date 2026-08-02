# Redis Interview Cheat Sheet

## Overview

This cheat sheet is a rapid revision guide for Redis interviews. It focuses on the concepts, commands, architecture, performance, and production knowledge that senior backend engineers are expected to know.

---

# Redis in One Minute

- In-memory NoSQL data store
- Key-Value database
- Single-threaded event-driven architecture
- Extremely low latency (<1 ms)
- Supports multiple data structures
- Optional persistence
- Replication support
- High Availability with Sentinel
- Horizontal scaling using Redis Cluster

---

# Redis vs Traditional Databases

| Feature | Redis | Relational Database |
|---------|-------|---------------------|
| Storage | Memory (optional disk persistence) | Disk |
| Speed | Extremely Fast | Slower |
| Schema | Schema-less | Fixed Schema |
| Transactions | Limited | Full ACID |
| Scaling | Horizontal (Cluster) | Typically Vertical |
| Best Use | Cache, Session, Queue | Persistent Business Data |

---

# Redis Data Structures

| Structure | Best For |
|------------|-----------|
| String | Cache, Counters |
| Hash | Objects, User Profiles |
| List | Queues |
| Set | Unique Collections |
| Sorted Set | Leaderboards |
| Stream | Event Processing |
| Bitmap | Feature Flags |
| HyperLogLog | Unique Counting |
| Geospatial | Nearby Search |

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
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
| SCAN | Incremental |
| KEYS | O(N) |

---

# Commands Every Engineer Should Know

```bash
SET

GET

DEL

EXPIRE

TTL

HSET

HGET

LPUSH

RPUSH

LPOP

SADD

SMEMBERS

ZADD

ZRANGE

SCAN

INFO

SLOWLOG GET

CLIENT LIST

MONITOR
```

---

# Persistence

## RDB

- Snapshot based
- Faster recovery
- Lower runtime overhead
- Possible data loss between snapshots

---

## AOF

- Logs every write
- Better durability
- Larger disk usage
- Slightly slower writes

---

## Best Practice

```
RDB

+

AOF

↓

Production
```

---

# Replication

```
        Master
       /      \
      ▼        ▼
 Replica1   Replica2
```

Benefits

- High availability
- Read scaling
- Backup copy

---

# Sentinel

Purpose

- Monitor Redis
- Detect failures
- Automatic failover
- Service discovery

---

# Redis Cluster

```
Master

↓

Replica

Master

↓

Replica

Master

↓

Replica
```

Provides

- Horizontal scaling
- Sharding
- Automatic failover

---

# Memory Management

Important commands

```bash
INFO MEMORY

MEMORY STATS

MEMORY USAGE key

MEMORY DOCTOR
```

---

# Eviction Policies

| Policy | Description |
|----------|-------------|
| noeviction | Reject writes |
| allkeys-lru | Least Recently Used |
| allkeys-lfu | Least Frequently Used |
| volatile-lru | Expiring keys only |
| volatile-ttl | Shortest TTL first |

---

# Performance Best Practices

- Prefer O(1) operations.
- Use Hashes instead of huge JSON strings.
- Use connection pooling.
- Use pipelining.
- Configure TTLs.
- Monitor memory.
- Avoid blocking commands.
- Use Redis Cluster for large deployments.

---

# Dangerous Commands

| Command | Reason |
|----------|--------|
| KEYS | Blocks Redis |
| FLUSHALL | Deletes everything |
| FLUSHDB | Deletes database |
| MONITOR | Heavy overhead |
| DEBUG | Administrative only |

---

# Monitoring Commands

```bash
INFO

INFO MEMORY

INFO CPU

INFO STATS

INFO REPLICATION

CLIENT LIST

LATENCY DOCTOR

SLOWLOG GET
```

---

# Common Production Problems

| Problem | Solution |
|----------|----------|
| High CPU | Remove expensive commands |
| High Memory | Optimize data model |
| Slow Responses | Review Slow Log |
| Replica Lag | Check network and write load |
| Frequent Evictions | Increase memory or adjust eviction policy |
| Hot Keys | Shard or cache locally |

---

# Caching Patterns

| Pattern | Description |
|----------|-------------|
| Cache Aside | Application manages cache |
| Read Through | Cache loads data automatically |
| Write Through | Write to cache and database together |
| Write Behind | Async database updates |

---

# Common Use Cases

- API Response Cache
- Session Store
- Leaderboards
- Rate Limiting
- Shopping Cart
- Distributed Locking
- Real-time Analytics
- Pub/Sub Messaging
- Event Streaming

---

# Redis vs Memcached

| Feature | Redis | Memcached |
|----------|-------|-----------|
| Persistence | Yes | No |
| Replication | Yes | No |
| Cluster | Yes | Limited |
| Data Structures | Many | String Only |
| Pub/Sub | Yes | No |
| Streams | Yes | No |

---

# Frequently Asked Interview Questions

| Question | Short Answer |
|-----------|--------------|
| Why is Redis fast? | In-memory, efficient data structures, event-driven architecture |
| Why single-threaded? | Simpler concurrency model with excellent performance |
| What is Redis used for? | Cache, sessions, queues, analytics, messaging |
| Difference between RDB and AOF? | Snapshot vs append-only log |
| Sentinel vs Cluster? | HA vs HA + horizontal scaling |
| Why SCAN instead of KEYS? | Non-blocking incremental iteration |
| What is pipelining? | Batch multiple commands in one network round trip |
| What are hot keys? | Frequently accessed keys causing uneven load |
| What is cache penetration? | Requests for non-existent data repeatedly hitting the database |
| What is cache stampede? | Many clients rebuilding an expired cache simultaneously |

---

# Senior-Level Questions

Be prepared to explain:

- How Redis achieves high performance.
- How replication works internally.
- How failover occurs in Sentinel.
- How Redis Cluster shards data.
- Why `SCAN` is preferred over `KEYS`.
- How to investigate memory fragmentation.
- How to troubleshoot high latency.
- When to use Streams instead of Pub/Sub.
- How distributed locking works with Redis.
- Cache consistency strategies.
- Hot key mitigation techniques.
- Persistence trade-offs in production.

---

# 30-Second Revision

```text
Redis

↓

In-memory Key-Value Store

↓

Fast (<1 ms)

↓

Strings
Hashes
Lists
Sets
Sorted Sets
Streams
Bitmaps
HyperLogLog
Geospatial

↓

Persistence
RDB + AOF

↓

Replication

↓

Sentinel

↓

Cluster

↓

Monitoring

↓

INFO
SLOWLOG
LATENCY
MEMORY

↓

Best Practices

SCAN > KEYS

TTL

Connection Pool

Pipeline

Monitor Continuously
```

---

# Interview Success Checklist

Before attending a Redis interview, ensure you can confidently explain:

- ✅ Why Redis is fast
- ✅ All Redis data structures and their use cases
- ✅ Time complexity of common operations
- ✅ RDB vs AOF
- ✅ Replication, Sentinel, and Cluster
- ✅ Memory management and eviction policies
- ✅ Cache patterns and cache invalidation
- ✅ Performance optimization techniques
- ✅ Monitoring and troubleshooting commands
- ✅ Real-world production architectures
- ✅ Common failure scenarios and recovery strategies
- ✅ Redis integration with backend frameworks such as Django and FastAPI