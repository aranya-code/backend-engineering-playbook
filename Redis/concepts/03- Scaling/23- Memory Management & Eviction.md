# Memory Management & Eviction

## Overview

Redis is an **in-memory database**, meaning that all active data is stored in RAM rather than on disk. This design makes Redis exceptionally fast, with operations often completing in microseconds. However, RAM is a finite and relatively expensive resource.

As applications grow, Redis eventually reaches its configured memory limit. At that point, Redis must decide how to handle incoming data. It can reject new writes, remove old data, or evict less useful keys based on a configurable eviction policy.

Understanding Redis memory management is critical for designing reliable, high-performance systems. Poor memory configuration can lead to cache misses, increased latency, application failures, or even Redis crashes.

---

# Why Memory Management Matters

Consider an application using Redis as a cache.

```
Redis Memory

↓

16 GB
```

After months of operation:

```
Current Usage

↓

15.9 GB
```

Eventually:

```
16 GB

↓

Memory Full
```

A new request arrives.

Without a memory management strategy:

```
Cannot Store Data

↓

Application Errors
```

Redis therefore needs policies to determine what happens when memory becomes full.

---

# Redis Memory Model

Redis stores almost everything in RAM.

```
Application

↓

Redis

↓

RAM

↓

Microsecond Access
```

Unlike traditional databases:

```
Application

↓

Disk

↓

Milliseconds
```

RAM provides significantly lower latency but has limited capacity.

---

# Components of Redis Memory

Redis memory is used for more than just keys and values.

```
Total Memory

↓

Keys

↓

Values

↓

Metadata

↓

Replication Buffers

↓

Client Connections

↓

Internal Structures
```

The actual memory consumption is often larger than the raw data size.

---

# Memory Usage Example

Suppose we store:

```
User Profile

↓

1 KB
```

Redis may consume:

```
Key

↓

Value

↓

Metadata

↓

Pointers

↓

Allocator Overhead
```

Actual memory usage could exceed 1 KB.

---

# Memory Overhead

Every Redis object contains internal metadata.

Example:

```
String

↓

Value

+

Object Metadata

+

Memory Allocator Data
```

Small values may consume considerably more memory than expected.

---

# Configuring Memory Limits

Redis allows administrators to define a maximum memory limit.

Conceptually:

```
Available RAM

↓

64 GB

↓

Redis Limit

↓

48 GB
```

Leaving unused RAM prevents operating system instability and allows room for background operations.

---

# What Happens When Memory Is Full?

Once Redis reaches the configured limit:

```
Memory Full

↓

Incoming Write
```

Redis follows the configured eviction policy.

Possible outcomes:

```
Reject Write
```

or

```
Remove Existing Keys

↓

Store New Data
```

---

# Eviction

Eviction is the process of removing keys to free memory.

```
Memory Full

↓

Select Key

↓

Delete Key

↓

Store New Data
```

Choosing the correct eviction policy is one of the most important production decisions.

---

# Eviction Policies

Redis supports multiple eviction strategies.

```
Memory Full

↓

Choose Policy

↓

Remove Keys
```

Each policy is designed for different workloads.

---

# noeviction

Behavior:

```
Memory Full

↓

Reject New Writes
```

Existing data remains untouched.

Characteristics:

- No automatic deletion
- Predictable
- Suitable for persistent datasets

Best suited for:

- Financial systems
- Configuration stores
- Critical business data

---

# allkeys-lru

Least Recently Used (LRU).

```
Memory Full

↓

Least Recently Used Key

↓

Evict
```

Frequently accessed data remains in memory.

Ideal for:

- Web caches
- API response caching
- Session caching

---

# volatile-lru

Only keys with expiration times are considered.

```
Memory Full

↓

TTL Keys

↓

Least Recently Used

↓

Evict
```

Persistent keys remain untouched.

Useful when only cached data has expiration.

---

# allkeys-lfu

Least Frequently Used (LFU).

```
Memory Full

↓

Lowest Access Count

↓

Evict
```

Keys that are rarely accessed are removed first.

Suitable for:

- Recommendation systems
- AI inference caches
- Product catalogs

---

# volatile-lfu

Similar to LFU but only affects keys with expiration.

```
TTL Keys

↓

Lowest Frequency

↓

Evict
```

Persistent keys are protected.

---

# allkeys-random

Redis removes a random key.

```
Memory Full

↓

Random Key

↓

Delete
```

Simple but unpredictable.

Rarely used in production.

---

# volatile-random

Random eviction only among keys with expiration.

```
TTL Keys

↓

Random Selection

↓

Delete
```

---

# volatile-ttl

Redis removes the key closest to expiration.

```
Memory Full

↓

Shortest Remaining TTL

↓

Delete
```

Useful when keys naturally expire soon.

---

# Eviction Policy Comparison

| Policy | Deletes Keys | Uses TTL | Typical Use Case |
|----------|--------------|-----------|------------------|
| noeviction | No | No | Persistent data |
| allkeys-lru | Yes | No | General caching |
| volatile-lru | Yes | Yes | Expiring cache |
| allkeys-lfu | Yes | No | Frequently accessed data |
| volatile-lfu | Yes | Yes | Expiring hot data |
| allkeys-random | Yes | No | Testing |
| volatile-random | Yes | Yes | Specialized workloads |
| volatile-ttl | Yes | Yes | TTL-driven cache |

---

# LRU (Least Recently Used)

LRU assumes:

```
Recently Used

↓

Likely Needed Again
```

Example:

```
User Sessions

↓

Frequently Accessed

↓

Remain
```

Old inactive sessions are removed first.

---

# LFU (Least Frequently Used)

LFU assumes:

```
Frequently Accessed

↓

More Valuable
```

Example:

```
Popular Products

↓

Millions of Requests

↓

Remain
```

Rarely viewed products are evicted.

---

# LRU vs LFU

| Feature | LRU | LFU |
|----------|-----|-----|
| Based On | Recent Access | Access Frequency |
| Learns Popularity | No | Yes |
| Better for Trending Data | Yes | Moderate |
| Better for Stable Popular Data | Moderate | Yes |

Choose the strategy based on application behavior.

---

# Expiring Keys

Many Redis applications rely on TTL.

```
Session

↓

30 Minutes

↓

Automatically Removed
```

Expired keys free memory naturally.

This often reduces eviction frequency.

---

# Memory Fragmentation

Memory fragmentation occurs when:

```
Allocated Memory

↓

Partially Used

↓

Unused Gaps
```

Redis may appear to use more memory than the actual dataset requires.

Fragmentation is managed by the memory allocator but should still be monitored.

---

# Lazy Freeing

Deleting very large objects immediately can block Redis.

Instead:

```
Delete Request

↓

Background Memory Cleanup
```

This improves responsiveness under heavy workloads.

---

# Memory Monitoring

Production Redis deployments should continuously monitor:

- Used memory
- Peak memory
- Fragmentation ratio
- Evicted keys
- Expired keys
- Connected clients
- Replication buffers

These metrics help identify capacity issues before they affect users.

---

# Capacity Planning

Suppose an application currently stores:

```
100 GB
```

Expected annual growth:

```
50%
```

Next year:

```
150 GB
```

Infrastructure should be sized for future growth rather than current usage alone.

---

# Common Production Use Cases

Memory management is critical for:

- Session stores
- API caching
- AI inference caching
- Recommendation engines
- Shopping carts
- Real-time analytics
- Gaming leaderboards
- Authentication tokens
- CDN edge caching
- IoT telemetry

---

# Common Mistakes

## No Memory Limit

Allowing Redis to consume all available RAM can cause:

```
Operating System

↓

Out of Memory

↓

OOM Killer

↓

Redis Terminated
```

Always configure an appropriate memory limit.

---

## Wrong Eviction Policy

Choosing:

```
Random Eviction
```

for a cache containing hot data may significantly reduce cache hit rates.

Select the policy according to access patterns.

---

## Ignoring Fragmentation

High fragmentation wastes memory and reduces effective capacity.

Monitor fragmentation ratios regularly.

---

## Storing Large Objects

Very large values:

```
Huge JSON

↓

Large Memory

↓

Long Deletion Time
```

Break large datasets into smaller logical units whenever possible.

---

# Best Practices

- Configure a maximum memory limit.
- Select an eviction policy appropriate for the workload.
- Monitor memory usage continuously.
- Use TTL for temporary data.
- Avoid storing excessively large objects.
- Monitor eviction and expiration statistics.
- Plan capacity well before memory becomes full.

---

# Production Considerations

When deploying Redis in production:

- Reserve RAM for the operating system.
- Continuously monitor memory metrics.
- Test eviction policies under load.
- Benchmark cache hit ratios.
- Monitor fragmentation and allocator performance.
- Review application access patterns periodically.
- Scale horizontally before memory becomes a bottleneck.

---

# Memory Management in Production Architecture

```
                API Gateway
                     │
          +----------+----------+
          │                     │
   User Service         Order Service
          │                     │
          +----------+----------+
                     │
                 Redis Cache
                     │
        +------------+------------+
        │                         │
    Memory Limit            Eviction Policy
        │                         │
        +------------+------------+
                     │
                 Application
```

Applications rely on Redis to manage memory efficiently while maintaining low latency and predictable performance.

---

# Summary

Memory management is one of the most important operational aspects of Redis. Since Redis stores active data in RAM, careful planning is required to prevent memory exhaustion and maintain consistent performance. Redis provides configurable memory limits and multiple eviction policies, allowing applications to balance performance, reliability, and resource utilization. Choosing the appropriate eviction strategy, monitoring memory usage, and planning for future growth are essential for running Redis successfully in production.

---

# Key Takeaways

- Redis stores active data in memory, making RAM a critical resource.
- Configure a maximum memory limit to prevent system instability.
- Eviction policies determine how Redis behaves when memory becomes full.
- LRU favors recently used data, while LFU favors frequently accessed data.
- Monitor fragmentation, evictions, expiration rates, and overall memory usage.
- Use TTL for temporary data to reduce unnecessary memory consumption.
- Proper memory management is essential for scalable, reliable Redis deployments.