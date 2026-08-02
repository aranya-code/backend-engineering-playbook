# Cache Consistency

## Overview

One of the biggest challenges in distributed systems is ensuring that **the cache and the database contain the same data**.

Since Redis is typically used as a performance layer rather than the source of truth, there is always a possibility that cached data becomes **stale**, **outdated**, or **inconsistent** with the underlying database.

This challenge is known as **Cache Consistency**.

Maintaining perfect consistency while preserving high performance is extremely difficult, and every caching strategy involves trade-offs between:

- Performance
- Availability
- Consistency
- Cost
- Complexity

Large-scale systems such as Amazon, Netflix, Uber, and Facebook all implement carefully designed cache consistency strategies based on their business requirements.

---

# What is Cache Consistency?

A cache is considered **consistent** when the data stored in Redis accurately reflects the latest state of the database.

```
             Database

      Product Price = $100

               │

               ▼

              Redis

      Product Price = $100
```

Both contain identical data.

---

# Inconsistent Cache

Suppose a product price changes.

```
Database

↓

Price = $120
```

Redis still contains

```
Price = $100
```

Users receive outdated information.

```
Client

↓

Redis

↓

Old Data
```

---

# Why Inconsistency Happens

Consider a simple update.

```
Application

↓

Database Updated

↓

Redis Still Old

↓

Client Reads Cache
```

The cache was never updated.

---

# Typical Read Flow

```
Client

↓

Redis

↓

Hit?

├── Yes

│      ↓

│ Return Cached Data

│

└── No

↓

Database

↓

Redis

↓

Client
```

---

# Typical Write Flow

```
Update Request

↓

Database

↓

Redis

↓

Success
```

The challenge is keeping these two operations synchronized.

---

# Causes of Cache Inconsistency

Common causes include:

- Missing cache invalidation
- Delayed cache updates
- Concurrent writes
- Network failures
- Redis outages
- Database failures
- Replication lag
- Race conditions
- Multiple application instances

---

# Example 1 — Missing Cache Invalidation

```
Product

↓

Price = $100

↓

Cached
```

Administrator updates the price.

```
Database

↓

$120
```

Redis remains

```
$100
```

Users continue seeing the old price.

---

# Example 2 — Concurrent Updates

```
Thread A

↓

Price = $120
```

Simultaneously

```
Thread B

↓

Price = $130
```

Redis may receive updates in the wrong order.

Final state

```
Database

↓

130

Redis

↓

120
```

---

# Example 3 — Database Success, Cache Failure

```
Update

↓

Database Updated

↓

Redis Update Failed
```

Now

```
Database

↓

New Data

Redis

↓

Old Data
```

---

# Example 4 — Cache Success, Database Failure

```
Redis Updated

↓

Database Failed
```

Redis contains information that never actually reached the database.

---

# Strong Consistency

```
Database

↓

Redis Updated

↓

Return Success
```

Users never receive stale data.

Advantages

- Correct data
- Predictable behavior

Disadvantages

- Higher latency
- More complexity

Typical examples:

- Banking
- Payment processing
- Medical systems

---

# Eventual Consistency

```
Database Updated

↓

Redis Updated Later

↓

Eventually Same
```

Temporary inconsistency is acceptable.

Advantages

- Better performance
- Higher throughput

Used by:

- Social media
- E-commerce
- Analytics
- Recommendation engines

---

# Read-After-Write Consistency

Suppose a user changes their email.

```
Update Email

↓

Read Email

↓

Latest Email
```

The user expects to immediately see their own changes.

Many applications require this guarantee.

---

# Consistency Strategies

## Strategy 1 — Cache Aside

```
Update Database

↓

Delete Cache

↓

Next Read

↓

Reload Cache
```

Most widely used strategy.

Advantages

- Simple
- Reliable

Disadvantages

First read after update is slower.

---

## Strategy 2 — Write Through

```
Application

↓

Redis Updated

↓

Database Updated
```

Both remain synchronized.

Advantages

- Strong consistency

Disadvantages

- Slower writes

---

## Strategy 3 — Write Behind

```
Redis Updated

↓

Background Worker

↓

Database Updated
```

High performance

But

```
Temporary Inconsistency
```

---

## Strategy 4 — Event-Based Cache Invalidation

```
Database Updated

↓

Publish Event

↓

Consumers

↓

Delete Cache
```

Very common in microservices.

---

# Event Architecture

```
Inventory Service

↓

Kafka

↓

Order Service

↓

Redis

↓

Cache Invalidated
```

Every service refreshes independently.

---

# Strategy 5 — Versioned Cache Keys

Instead of

```
product:100
```

Use

```
product:v2:100
```

Schema changes automatically create new cache entries.

Old cache naturally expires.

---

# Strategy 6 — TTL

```
Redis

↓

TTL

↓

Expiration

↓

Reload
```

Even forgotten cache entries eventually disappear.

TTL alone is **not** a consistency strategy but helps limit stale data.

---

# Strategy 7 — Optimistic Locking

```
Read Version

↓

Update

↓

Version Changed?

↓

Retry
```

Useful for concurrent updates.

---

# Strategy 8 — Distributed Transactions

```
Redis

↓

Database

↓

Commit

↓

Success
```

Rarely used because of high complexity and poor scalability.

---

# Race Condition Example

Consider two users updating the same product.

```
User A

↓

Database

↓

Redis
```

At the same time

```
User B

↓

Database

↓

Redis
```

Improper ordering can overwrite newer data.

Solutions

- Version numbers
- Optimistic locking
- Event ordering

---

# Cache Invalidation

One of the most important concepts.

```
Update

↓

Delete Cache

↓

Next Read

↓

Fresh Cache
```

Many engineers summarize caching with the famous quote:

> **"There are only two hard things in Computer Science: cache invalidation and naming things."**

---

# Real-World Example

## Product Price

```
Admin

↓

Update Price

↓

Database

↓

Delete Cache

↓

Customer Reads

↓

Fresh Price
```

---

## Banking

```
Transfer

↓

Database

↓

Redis

↓

Customer Balance
```

Strong consistency is mandatory.

---

## Social Media

```
New Like

↓

Database

↓

Redis Updated Later
```

A short delay is acceptable.

---

## E-commerce

```
Inventory Updated

↓

Event

↓

Redis Invalidated

↓

Fresh Inventory
```

---

# Cache Consistency in Microservices

```
Inventory Service

↓

Kafka

↓

Order Service

↓

Catalog Service

↓

Redis
```

Each service updates its own cache based on events.

---

# Common Production Use Cases

Consistency strategies are important for:

- Product pricing
- Inventory
- Banking
- User profiles
- Shopping carts
- Permissions
- Authentication
- Recommendation systems
- CMS platforms
- Configuration services

---

# Common Mistakes

## Updating Database Only

```
Database

↓

Updated

↓

Redis

↓

Old
```

Always invalidate or update the cache.

---

## Long TTL

```
Old Cache

↓

24 Hours
```

Users receive outdated information.

---

## Ignoring Race Conditions

Concurrent updates require synchronization.

---

## No Retry Logic

Cache update failures should trigger retries or compensation mechanisms.

---

## Treating Redis as Source of Truth

Redis should generally be considered a **performance optimization**, not the authoritative datastore.

---

# Best Practices

- Use Cache Aside for most web applications.
- Delete or update cache immediately after successful database writes.
- Keep TTLs appropriate for the volatility of the data.
- Use event-driven invalidation in microservice architectures.
- Apply optimistic locking where concurrent updates are common.
- Use versioned cache keys when cache formats change.
- Monitor cache hit ratio, stale reads, and update failures.
- Design applications to tolerate brief inconsistencies where business requirements permit.

---

# Performance Considerations

| Strategy | Read Speed | Write Speed | Consistency |
|----------|------------|-------------|-------------|
| Cache Aside | Excellent | Excellent | Good |
| Write Through | Excellent | Moderate | Excellent |
| Write Behind | Excellent | Excellent | Eventual |
| Event Invalidation | Excellent | Excellent | Good |
| Distributed Transaction | Moderate | Poor | Excellent |

---

# Production Considerations

For production deployments:

- Decide upfront whether your application requires **strong** or **eventual** consistency.
- Never use the same consistency strategy for every type of data—business requirements differ.
- Ensure cache invalidation occurs only after successful database commits.
- Use message brokers (Kafka, RabbitMQ, Redis Streams) for reliable event-driven invalidation.
- Monitor cache update failures, replication lag, stale read frequency, and cache hit ratio.
- Build retry mechanisms and dead-letter queues for failed cache synchronization events.
- Regularly test failure scenarios such as Redis outages, database failures, and concurrent updates.

---

# Decision Guide

| Scenario | Recommended Strategy |
|----------|----------------------|
| Product Catalog | Cache Aside |
| User Profiles | Write Through |
| Shopping Cart | Write Through |
| Banking | Strong Consistency |
| Inventory | Event-Based Invalidation |
| Analytics | Write Behind |
| Social Media Feed | Eventual Consistency |
| Configuration | Cache Aside + TTL |

---

# Summary

Cache consistency is the challenge of keeping Redis synchronized with the underlying database while maintaining high performance and scalability. Because Redis is typically a cache rather than the source of truth, stale data can arise from missed invalidations, concurrent updates, failures, or replication delays. Different workloads require different consistency models—strong consistency for financial systems, eventual consistency for social media and analytics, and hybrid approaches for most web applications. Choosing the right strategy and implementing robust invalidation, monitoring, and failure handling are essential for production-grade distributed systems.

---

# Key Takeaways

- Cache consistency ensures Redis reflects the latest database state.
- Perfect consistency often comes at the cost of performance and complexity.
- Cache Aside remains the most common strategy for web applications.
- Write Through provides stronger consistency but slower writes.
- Write Behind offers high throughput with eventual consistency.
- Event-driven invalidation is widely used in microservice architectures.
- Monitor stale reads, cache update failures, and replication lag in production.
- Select consistency strategies based on business requirements rather than applying a single approach everywhere.