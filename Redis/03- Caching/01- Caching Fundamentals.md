# Caching Fundamentals

## Overview

Caching is one of the most important techniques used in modern backend systems to improve performance, reduce latency, increase throughput, and decrease database load.

Instead of repeatedly querying a slow backend such as a relational database, applications store frequently accessed data in a high-speed cache like Redis. Subsequent requests are served directly from memory, resulting in response times measured in microseconds rather than milliseconds.

Caching is a foundational concept used in virtually every large-scale application, including:

- Google Search
- Amazon
- Netflix
- Facebook
- Instagram
- Uber
- Spotify
- LinkedIn

Redis has become the industry-standard distributed cache because of its in-memory architecture, rich data structures, high throughput, and simplicity.

---

# Why Caching Matters

Consider an application without caching.

```
                Client
                   │
                   ▼
            Application Server
                   │
                   ▼
              Database Query
                   │
                   ▼
             Database Response
                   │
                   ▼
              Return Response
```

Every request reaches the database.

Problems include:

- High latency
- Increased database load
- Poor scalability
- Expensive infrastructure
- Slow user experience

---

Now introduce Redis.

```
                Client
                   │
                   ▼
            Application Server
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
     Redis Cache         Database
         │                   │
         └─────────┬─────────┘
                   ▼
              Return Response
```

Frequently accessed data never reaches the database.

---

# What is a Cache?

A cache is a temporary storage layer that stores frequently accessed data closer to the application.

Characteristics:

- Extremely fast
- Temporary
- Memory-based
- Frequently accessed
- Can expire automatically
- Easily rebuilt

Caches improve:

- Response time
- Throughput
- User experience
- Scalability

---

# Why Redis?

Redis stores data entirely in memory.

Approximate latency comparison:

| Storage | Typical Latency |
|----------|----------------:|
| CPU Cache | ~1 ns |
| RAM (Redis) | ~100 ns |
| NVMe SSD | ~100 µs |
| HDD | ~5 ms |
| Database Query | 1–100 ms |

Even a well-optimized database is significantly slower than an in-memory cache.

---

# How Caching Works

```
User Request

↓

Application

↓

Cache Lookup

↓

Cache Hit?

 ├── Yes
 │      ↓
 │   Return Cached Data
 │
 └── No
        ↓
    Query Database
        ↓
    Store in Cache
        ↓
    Return Response
```

This is the basic workflow used by almost every backend system.

---

# Cache Hit

A Cache Hit occurs when requested data already exists in Redis.

```
User

↓

Redis

↓

Data Found

↓

Response
```

Advantages:

- Extremely fast
- No database access
- Lower latency
- Lower cost

---

# Cache Miss

A Cache Miss occurs when Redis doesn't contain the requested data.

```
User

↓

Redis

↓

Not Found

↓

Database

↓

Redis

↓

User
```

The application stores the retrieved data in Redis for future requests.

---

# Cache Hit Ratio

One of the most important caching metrics.

Formula

```
Cache Hit Ratio

=

Cache Hits

-----------------------

Hits + Misses
```

Example

```
Requests

1000

↓

Hits

950

↓

Misses

50

↓

Hit Ratio

95%
```

Higher hit ratios indicate better cache efficiency.

Typical production targets:

| Hit Ratio | Quality |
|------------|----------|
| 50% | Poor |
| 70% | Acceptable |
| 85% | Good |
| 95%+ | Excellent |

---

# Why Not Cache Everything?

Caching everything sounds attractive but introduces problems.

```
Large Dataset

↓

Redis Memory

↓

Expensive

↓

Evictions

↓

Poor Performance
```

Not all data benefits from caching.

Good candidates:

- Product catalog
- User profile
- Configuration
- API responses
- Search results
- Popular articles

Poor candidates:

- Frequently changing data
- Large binary files
- Rarely accessed records
- Sensitive information with strict consistency requirements

---

# Benefits of Caching

## Reduced Database Load

```
Without Cache

100,000 Requests

↓

100,000 Database Queries
```

With Redis

```
100,000 Requests

↓

95,000 Cache Hits

↓

5,000 Database Queries
```

Database workload is dramatically reduced.

---

## Lower Latency

Typical request

```
Database

↓

25 ms
```

Redis

```
Redis

↓

0.2 ms
```

Users experience much faster response times.

---

## Better Scalability

```
Millions of Users

↓

Redis Cluster

↓

Database Protected
```

Redis absorbs read traffic, allowing databases to scale more efficiently.

---

## Cost Reduction

```
Fewer Database Servers

↓

Lower Cloud Costs
```

Caching often reduces infrastructure expenses.

---

# Common Types of Cached Data

Applications commonly cache:

- User sessions
- Product information
- Categories
- Search results
- Dashboard statistics
- Configuration
- Permissions
- JWT blacklists
- Feature flags
- API responses
- Frequently viewed content

---

# What Should Not Be Cached

Avoid caching:

- Passwords
- Encryption keys
- Rapidly changing stock prices (without strategy)
- Highly transactional financial balances
- Frequently updated inventory counts
- Massive media files
- One-time operations

---

# Cache Lifecycle

```
Database

↓

Read Data

↓

Store in Redis

↓

Serve Requests

↓

TTL Expires

↓

Removed

↓

Reload When Needed
```

---

# Cache Expiration

Most cache entries should expire automatically.

```
Store Data

↓

TTL

↓

Redis

↓

Automatic Removal
```

Expiration prevents stale data from living forever.

---

# Cache Warming

Instead of waiting for users to populate the cache, applications can preload frequently used data.

```
Application Startup

↓

Load Popular Data

↓

Redis

↓

Ready Before Users Arrive
```

Examples:

- Product catalog
- Configuration
- Country lists
- Currency exchange rates
- Popular pages

---

# Cache Invalidation

Eventually cached data becomes outdated.

```
Database Updated

↓

Redis Cache

↓

Invalidate

↓

Next Request

↓

Fresh Data
```

One of the hardest problems in distributed systems.

Later chapters explore this in depth.

---

# Common Production Use Cases

Caching is widely used for:

- REST APIs
- GraphQL APIs
- Authentication
- Session storage
- Shopping carts
- Product catalogs
- User preferences
- Analytics dashboards
- Recommendation systems
- Content Management Systems (CMS)

---

# Common Mistakes

## Caching Everything

```
Everything Cached

↓

Memory Full

↓

Evictions

↓

Lower Performance
```

Cache only valuable data.

---

## No Expiration

```
Old Data

↓

Never Removed

↓

Users Receive Stale Results
```

Always define a cache invalidation strategy.

---

## Ignoring Hit Ratio

Applications should continuously monitor:

- Cache hit ratio
- Miss ratio
- Eviction count
- Memory usage
- Latency

---

## Using Cache as Primary Storage

Redis cache is not a replacement for a database.

```
Database

↓

Source of Truth

↓

Redis

↓

Performance Layer
```

---

# Best Practices

- Cache frequently accessed data.
- Keep cached objects relatively small.
- Set appropriate TTL values.
- Monitor hit ratio and evictions.
- Use descriptive key naming.
- Store IDs instead of large objects when possible.
- Avoid caching highly volatile data unless necessary.
- Choose the appropriate caching pattern for each workload.

---

# Performance Considerations

Factors affecting cache performance include:

| Factor | Impact |
|---------|--------|
| Hit Ratio | Higher is better |
| Memory Size | Larger caches improve hit rates |
| Object Size | Smaller objects perform better |
| TTL Strategy | Prevents stale data |
| Eviction Policy | Influences cache effectiveness |
| Network Latency | Keep Redis close to the application |

---

# Production Considerations

For production deployments:

- Size Redis appropriately based on your working dataset rather than total dataset size.
- Monitor key metrics such as hit ratio, eviction rate, memory fragmentation, and latency.
- Define TTL policies for every cacheable object.
- Implement cache warming for frequently accessed datasets after deployments or restarts.
- Plan for cache failures—applications should continue functioning even if Redis becomes unavailable.
- Avoid creating a single "hot key" that receives disproportionate traffic.
- Use Redis Cluster or replication for high availability and scalability.

---

# Caching Patterns Covered in This Module

The following chapters explore the most common caching strategies used in production:

| Pattern | Purpose |
|---------|---------|
| Cache Aside | Application-managed cache |
| Read Through | Cache loads data automatically |
| Write Through | Cache and database updated together |
| Write Behind | Asynchronous database updates |
| Refresh Ahead | Refresh before expiration |

Additional production topics include:

- Cache Eviction Strategies
- Cache Stampede
- Cache Avalanche
- Cache Penetration
- Cache Consistency
- Hot Keys
- Rate Limiting
- Real-World Caching Architectures

---

# Summary

Caching is a critical performance optimization technique that enables modern applications to serve frequently requested data directly from memory instead of repeatedly querying slower backend systems. Redis has become the industry standard for distributed caching because of its speed, flexibility, and scalability. Understanding cache hits, misses, expiration policies, invalidation strategies, and cache selection criteria is essential before implementing advanced caching patterns. The remaining chapters in this module build upon these fundamentals to cover the production-grade caching strategies used by companies operating at internet scale.

---

# Key Takeaways

- A cache stores frequently accessed data in memory to reduce latency.
- Redis is one of the fastest and most widely used distributed caching solutions.
- Cache hits avoid database queries, while cache misses load data from the database and populate the cache.
- Monitor cache hit ratio, memory usage, and eviction rates to evaluate cache effectiveness.
- Not every type of data should be cached; choose candidates carefully.
- Expiration and invalidation strategies are essential for maintaining data freshness.
- Redis should be treated as a performance layer, not the system of record.
- Advanced caching patterns such as Cache Aside, Read Through, and Write Through build on these core concepts.