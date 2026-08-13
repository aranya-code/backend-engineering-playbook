# 03 - DynamoDB Accelerator (DAX)

## Overview

Amazon DynamoDB Accelerator (DAX) is a **fully managed, in-memory cache** for DynamoDB that delivers **microsecond read latency** for read-intensive workloads.

Instead of every application request reaching DynamoDB, DAX stores frequently accessed items in memory and serves subsequent requests directly from the cache.

Unlike Amazon ElastiCache (Redis or Memcached), DAX is purpose-built for DynamoDB. It understands DynamoDB APIs and can often be integrated into existing applications with minimal code changes.

DAX is ideal for workloads with:

- High read traffic
- Frequently accessed ("hot") items
- Read-heavy applications
- Low-latency requirements
- Repeated access to the same data

Typical use cases include:

- Product catalogs
- Gaming leaderboards
- User profiles
- Content management systems
- News feeds
- Recommendation systems

---

# Why DAX Exists

Consider an online shopping website.

Every visitor requests:

```text
Product

↓

Price

↓

Images

↓

Description
```

Thousands of customers request the same product every second.

Without caching:

```text
Users

↓

Application

↓

DynamoDB

↓

Application

↓

Users
```

Every request consumes RCUs.

With DAX:

```text
Users

↓

Application

↓

DAX

↓

Cache Hit

↓

Users
```

Most requests never reach DynamoDB.

---

# Internal Architecture

```text
                 Application

                       │

               GetItem / Query

                       │

                DAX Cluster

         ┌─────────────┴─────────────┐

         ▼                           ▼

     Cache Hit                 Cache Miss

         │                           │

         ▼                           ▼

   Return Item               DynamoDB Table

                                     │

                                     ▼

                           Store Item in Cache

                                     │

                                     ▼

                              Return Response
```

---

# Cache Hit

A cache hit occurs when the requested item already exists in memory.

```text
Application

↓

DAX

↓

Item Found

↓

Return Immediately
```

Latency:

```text
Microseconds
```

No DynamoDB read occurs.

---

# Cache Miss

A cache miss occurs when the requested item is not cached.

```text
Application

↓

DAX

↓

Item Missing

↓

Read DynamoDB

↓

Store in Cache

↓

Return Item
```

Future requests become cache hits.

---

# Read-Through Cache

DAX implements a **read-through caching** strategy.

Workflow:

```text
Application

↓

Request Item

↓

DAX

↓

If Missing

↓

Read DynamoDB

↓

Cache Item

↓

Return Item
```

The application does not need separate cache management code.

---

# Write-Through Cache

When using DAX for writes:

```text
Application

↓

DAX

↓

Write DynamoDB

↓

Update Cache

↓

Return Success
```

This keeps the cache synchronized with DynamoDB.

---

# Supported Operations

DAX accelerates:

- GetItem
- BatchGetItem
- Query

It also supports:

- PutItem
- UpdateItem
- DeleteItem

However, its greatest performance benefit is for **read operations**.

---

# Eventually Consistent Reads

DAX provides:

```text
Eventually Consistent Reads
```

Applications requiring strongly consistent reads should bypass DAX and read directly from DynamoDB.

---

# DAX Cluster Architecture

A DAX cluster consists of:

```text
Primary Node

↓

Read Replicas
```

Example:

```text
        Primary

       /   |   \

 Replica Replica Replica
```

The primary coordinates writes while replicas handle read traffic.

---

# Automatic Failover

If the primary node fails:

```text
Primary

↓

Failure

↓

Replica Promoted

↓

Applications Continue
```

This process is managed automatically.

---

# Cache Invalidation

Suppose:

```text
Product Price

↓

Updated
```

Workflow:

```text
Update Request

↓

DAX

↓

Update DynamoDB

↓

Invalidate Cache

↓

Store Updated Item
```

Applications receive fresh data after the update.

---

# DAX vs DynamoDB

| Feature | DynamoDB | DAX |
|----------|----------|-----|
| Storage | Persistent | In-Memory Cache |
| Read Latency | Milliseconds | Microseconds |
| Data Source | Primary Database | Cached Data |
| Strong Consistency | Yes | No |
| Automatic Scaling | Yes | Cluster-Based |

---

# DAX vs Redis

| Feature | DAX | Redis |
|----------|-----|-------|
| Built for DynamoDB | ✅ | ❌ |
| API Compatibility | Native | Application Managed |
| Read-Through Cache | ✅ | Application Logic |
| Managed Cache Updates | ✅ | Manual |
| General Purpose Cache | ❌ | ✅ |

Redis is more flexible.

DAX is more specialized.

---

# Cache Workflow

```text
Application

↓

DAX

↓

Cache Hit?

↓

Yes

↓

Return Data

────────────

No

↓

Read DynamoDB

↓

Update Cache

↓

Return Data
```

---

# Real-World Example — Product Catalog

Popular product:

```text
iPhone

↓

Millions of Reads
```

Without DAX:

```text
Millions of DynamoDB Reads
```

With DAX:

```text
Millions of Cache Hits

↓

Very Few Database Reads
```

---

# Real-World Example — User Profiles

Every request requires:

```text
User Profile
```

Frequently accessed profiles remain in memory.

Result:

- Lower latency
- Lower RCU consumption
- Better user experience

---

# Real-World Example — Gaming

Leaderboard:

```text
Top Players
```

Thousands of players request rankings every second.

DAX serves leaderboard data from memory, dramatically reducing database load.

---

# Real-World Example — News Website

Homepage:

```text
Trending Articles

↓

Millions of Reads
```

DAX keeps popular content cached for fast delivery.

---

# Performance Considerations

DAX significantly improves:

- Read latency
- Throughput
- RCU consumption

However, it is less beneficial when:

- Every request reads different data
- Data changes continuously
- Strong consistency is required

Applications with poor cache hit rates may see little improvement.

---

# Best Practices

- Use DAX for read-heavy workloads.
- Cache frequently accessed items.
- Monitor cache hit ratio using CloudWatch.
- Use strongly consistent reads directly from DynamoDB when necessary.
- Deploy multiple DAX nodes for high availability.
- Benchmark performance before introducing DAX.

---

# Common Mistakes

## Using DAX for Write-Heavy Workloads

DAX primarily improves read performance.

Applications dominated by writes gain little benefit.

---

## Assuming Strong Consistency

DAX serves eventually consistent data.

Applications requiring the latest committed value should bypass DAX.

---

## Caching Rarely Accessed Data

If every request accesses unique items:

```text
Cache Miss

↓

Cache Miss

↓

Cache Miss
```

DAX provides minimal value.

---

## Ignoring Cache Metrics

Monitor:

- Cache Hit Rate
- Node CPU
- Memory Usage
- Network Throughput

Poor cache performance may indicate that DAX is unnecessary or improperly configured.

---

# Architecture Perspective

```text
                Client Request

                      │

                DAX Cluster

          ┌───────────┴───────────┐

          ▼                       ▼

     Cache Hit             Cache Miss

          │                       │

          ▼                       ▼

  Return Immediately      Read DynamoDB

                                  │

                                  ▼

                          Update Cache

                                  │

                                  ▼

                          Return Response
```

The objective is to maximize cache hits while minimizing database reads.

---

# Production Considerations

DAX is most valuable for applications with predictable read patterns and frequently accessed data.

Common production workloads include:

- E-commerce product catalogs
- Gaming leaderboards
- User profile services
- News portals
- Recommendation engines
- Session lookups
- Read-heavy APIs

Before introducing DAX, measure:

- Read latency
- RCU consumption
- Cache hit ratio
- Request distribution

In many cases, **Amazon ElastiCache (Redis)** provides greater flexibility for complex caching strategies, while DAX excels when accelerating DynamoDB access with minimal application changes.

---

# Interview Notes

A common interview question is:

> **What is DynamoDB Accelerator (DAX)?**

DAX is a fully managed, in-memory cache for DynamoDB that reduces read latency from milliseconds to microseconds by serving frequently accessed data directly from memory.

Another common question is:

> **Does DAX support strongly consistent reads?**

No. DAX serves eventually consistent reads. Applications that require strongly consistent data should read directly from DynamoDB.

Another common question is:

> **When should you use DAX instead of Redis?**

Use DAX when the goal is to accelerate DynamoDB reads with minimal code changes. Use Redis when you need a general-purpose cache supporting multiple data structures, custom caching strategies, or non-DynamoDB workloads.

Another common question is:

> **Does DAX reduce DynamoDB costs?**

Yes. By serving cache hits from memory, DAX reduces the number of read requests reaching DynamoDB, lowering RCU consumption for read-heavy workloads.

---

# Key Takeaways

- DAX is a fully managed, in-memory cache specifically designed for DynamoDB.
- It reduces read latency from milliseconds to microseconds for frequently accessed data.
- DAX uses read-through and write-through caching to simplify cache management.
- It is best suited for read-heavy workloads with high cache hit rates.
- DAX provides eventually consistent reads; strongly consistent reads must bypass the cache.
- Monitoring cache hit ratio and workload characteristics is essential to determine whether DAX delivers meaningful performance benefits.