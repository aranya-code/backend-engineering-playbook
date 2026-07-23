# 15 - DynamoDB Accelerator (DAX)

## Overview

As applications scale, database reads often become the primary performance bottleneck.

Consider a social media platform where millions of users continuously read the same trending post. Even though DynamoDB is capable of handling extremely high throughput, every request still requires:

- Network communication
- Request routing
- Partition lookup
- Item retrieval
- Response serialization

When the same data is requested repeatedly, performing identical database reads becomes inefficient.

This is where **DynamoDB Accelerator (DAX)** comes in.

DAX is a **fully managed, in-memory cache** built specifically for DynamoDB. It sits between your application and DynamoDB, storing frequently accessed items in memory to dramatically reduce read latency.

Instead of milliseconds, many reads can be served in **microseconds**.

---

# Why DAX Exists

Imagine an e-commerce application.

A product becomes the "Deal of the Day."

```text
Product X

↓

5 Million Reads
```

Without caching:

```text
Application

↓

DynamoDB

↓

Read Item

↓

Return Item
```

This process repeats millions of times for exactly the same data.

Although DynamoDB can scale, repeatedly reading identical data wastes capacity and increases latency.

A cache eliminates this unnecessary work.

---

# What is DAX?

DAX is an **in-memory caching layer** that is API-compatible with DynamoDB.

Applications communicate with DAX instead of DynamoDB.

```text
Application

      │

      ▼

     DAX

      │

      ▼

 DynamoDB
```

If data exists in the cache:

```text
Application

↓

DAX

↓

Response
```

No database request is required.

---

# Cache Hit vs Cache Miss

Every request results in one of two outcomes.

## Cache Hit

The requested item already exists in memory.

```text
Application

↓

DAX

↓

Memory

↓

Return Item
```

No call reaches DynamoDB.

Latency is typically measured in microseconds.

---

## Cache Miss

The item is not present in cache.

```text
Application

↓

DAX

↓

DynamoDB

↓

Return Item

↓

Store in Cache
```

Future requests are served directly from memory.

---

# Internal Request Flow

Without DAX

```text
Application

↓

DynamoDB

↓

Partition Lookup

↓

Read Item

↓

Return
```

With DAX

```text
Application

↓

DAX Cache

↓

Cache Hit?

↓

Yes

↓

Return Immediately
```

Only cache misses require DynamoDB access.

---

# Read-Through Caching

DAX automatically performs **read-through caching**.

Workflow:

```text
Read Request

↓

Cache Miss

↓

Retrieve from DynamoDB

↓

Store in Cache

↓

Return Response
```

Applications do not manually insert objects into the cache.

DAX manages cache population automatically.

---

# Write-Through Caching

When an application writes data:

```text
Application

↓

DAX

↓

DynamoDB

↓

Update Cache

↓

Return Success
```

This process is known as **write-through caching**.

Because DAX updates the cache immediately after a successful write, subsequent reads are more likely to retrieve the latest value.

---

# Cluster Architecture

DAX operates as a cluster rather than a single server.

```text
              DAX Cluster

         +-------------------+

         | Primary Node      |

         +-------------------+

             │      │

             ▼      ▼

      Replica      Replica

      Node         Node
```

The primary node processes write operations.

Replica nodes primarily serve read requests.

This architecture improves:

- Availability
- Scalability
- Fault tolerance

---

# DAX and High Availability

A production DAX cluster should span multiple Availability Zones.

```text
AZ-1

↓

Primary Node

---------------------

AZ-2

↓

Replica

---------------------

AZ-3

↓

Replica
```

If one node fails, another node can continue serving requests.

---

# Cache Consistency

Caching introduces an important question.

Suppose data changes.

```text
Price

$500

↓

Update

↓

$450
```

Should the cache immediately reflect the new value?

DAX updates cached items after successful writes through the DAX client.

However, if changes occur through another path (for example, directly via DynamoDB without using DAX), cached values may remain stale until they expire or are refreshed.

This is one reason DAX is best suited for workloads where occasional stale reads are acceptable.

---

# Time To Live (TTL) in DAX

Cached items do not remain in memory forever.

Each cached object has an expiration period.

```text
Read Item

↓

Cache

↓

TTL Expires

↓

Remove Item
```

Once expired:

```text
Next Request

↓

Retrieve from DynamoDB Again
```

Choosing an appropriate TTL balances:

- Freshness
- Memory usage
- Cache hit ratio

---

# DAX vs Application Caching

Many applications already use Redis or Memcached.

How is DAX different?

| Feature | DAX | Redis |
|---------|-----|--------|
| Purpose | DynamoDB Cache | General-Purpose Cache |
| API Compatible | ✅ Yes | ❌ No |
| Automatic Cache Population | ✅ Yes | ❌ Usually Manual |
| Fully Managed by AWS | ✅ Yes | Depends |
| Supports Non-DynamoDB Data | ❌ No | ✅ Yes |

Redis can cache anything.

DAX is optimized exclusively for DynamoDB.

---

# DAX vs ElastiCache

Another common comparison is DAX versus Amazon ElastiCache.

| Feature | DAX | ElastiCache |
|----------|-----|-------------|
| Purpose | DynamoDB Acceleration | General Caching Platform |
| Supports Redis | ❌ | ✅ |
| Supports Memcached | ❌ | ✅ |
| Automatic DynamoDB Integration | ✅ | ❌ |
| Requires Cache Logic | Minimal | Usually Yes |

Choose DAX when the goal is to accelerate DynamoDB with minimal application changes.

Choose ElastiCache when caching requirements extend beyond DynamoDB.

---

# When Should You Use DAX?

Excellent use cases include:

- Product catalogs
- Gaming leaderboards
- Social media feeds
- Trending content
- News articles
- Session lookups
- Frequently viewed user profiles

These workloads perform many more reads than writes.

---

# When Should You Avoid DAX?

Avoid DAX for workloads requiring:

- Strongly consistent reads
- Frequently changing data
- Financial transactions
- Inventory systems requiring immediate accuracy
- Write-heavy applications with low read reuse

In these scenarios, the benefits of caching are limited or stale data may be unacceptable.

---

# Performance Benefits

Typical latency comparison:

Without DAX

```text
5–10 ms
```

With DAX

```text
Microseconds
```

While exact performance depends on workload and infrastructure, DAX can dramatically reduce response times for read-heavy applications with high cache hit rates.

---

# Cost Considerations

Although DAX reduces DynamoDB read traffic, it introduces additional infrastructure costs.

You pay for:

- DAX cluster nodes
- Memory resources
- Network traffic

The cost is justified only if reduced latency or lower DynamoDB read consumption outweighs the expense.

Applications with low read volumes often gain little benefit.

---

# Best Practices

- Use DAX only for read-heavy workloads.
- Deploy clusters across multiple Availability Zones.
- Monitor cache hit ratios.
- Choose appropriate TTL values.
- Continue designing efficient partition keys.
- Benchmark performance before and after introducing DAX.
- Evaluate cost savings against cluster costs.

---

# Common Mistakes

## Using DAX for Write-Heavy Systems

If most requests are writes, cached data is rarely reused.

The performance improvement is minimal.

---

## Assuming DAX Replaces Good Schema Design

DAX accelerates reads.

It does not solve:

- Poor partition keys
- Hot partitions caused by writes
- Inefficient access patterns

---

## Expecting Strong Consistency

DAX is designed for high-performance reads.

Applications requiring strict read-after-write guarantees should evaluate whether DAX is appropriate for those operations.

---

## Caching Everything

Not every table benefits from caching.

Focus on frequently accessed, relatively stable data.

---

# Architecture Perspective

Typical production architecture:

```text
Users

↓

Load Balancer

↓

Application Servers

↓

DAX Cluster

↓

DynamoDB

↓

Storage Partitions
```

DAX reduces the number of requests reaching DynamoDB, improving both latency and database efficiency.

---

# Interview Notes

A common interview question is:

> **If DynamoDB already delivers single-digit millisecond latency, why would you introduce DAX?**

Because some applications require even lower latency or generate extremely high read traffic for the same data.

Rather than repeatedly querying DynamoDB, DAX serves frequently accessed items directly from memory. This reduces response times to microseconds, lowers DynamoDB read consumption, and helps absorb read hotspots.

Another common question is:

> **When would you choose Redis instead of DAX?**

Choose DAX when the primary goal is to accelerate DynamoDB with minimal application changes.

Choose Redis (or ElastiCache) when you need a general-purpose cache, shared cache across multiple data sources, advanced data structures, pub/sub messaging, distributed locking, or caching that is independent of DynamoDB.

---

# Key Takeaways

- DAX is a fully managed, in-memory cache designed specifically for DynamoDB.
- It reduces read latency from milliseconds to microseconds for cache hits.
- DAX performs automatic read-through and write-through caching.
- It is best suited for read-heavy workloads with frequently accessed data.
- DAX complements DynamoDB but does not replace good data modeling.
- Strongly consistent workloads and write-heavy systems typically gain less benefit from DAX.
- Understanding when **not** to use DAX is as important as knowing when it provides value.