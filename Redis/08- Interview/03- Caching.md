# Caching Interview Questions

## Overview

Caching is one of the most frequently discussed topics in backend interviews because it directly affects **application performance**, **scalability**, and **cost**.

Most applications spend significantly more time reading data than writing it. Redis is commonly introduced as a caching layer to reduce database load and improve response times.

Senior interviewers expect candidates to understand:

- Why caching is needed
- Cache patterns
- Cache invalidation
- Cache consistency
- Cache failures
- Production trade-offs
- Real-world architecture decisions

This chapter covers the most common Redis caching interview questions, from beginner to senior backend level.

---

# Q1. What is caching?

### Answer

Caching is the process of storing frequently accessed data in a fast storage layer so future requests can be served without accessing the primary database.

Architecture

```
Client

   │

   ▼

Application

   │

   ▼

Redis Cache

   │

Cache Miss

   │

   ▼

Database
```

Benefits

- Faster response time
- Reduced database load
- Lower infrastructure cost
- Higher scalability

---

# Q2. Why is Redis commonly used for caching?

### Answer

Redis is ideal for caching because it provides:

- In-memory storage
- Sub-millisecond latency
- Automatic expiration (TTL)
- Rich data structures
- High throughput
- Easy horizontal scaling

---

# Q3. What is a cache hit?

### Answer

A cache hit occurs when requested data is found in Redis.

```
Application

↓

Redis

↓

Data Found

↓

Response
```

The database is not accessed.

---

# Q4. What is a cache miss?

### Answer

A cache miss occurs when data is not available in Redis.

```
Application

↓

Redis

↓

Not Found

↓

Database

↓

Redis

↓

Client
```

The application fetches the data from the database and stores it in Redis for future requests.

---

# Q5. What is Cache Aside Pattern?

### Answer

Cache Aside (Lazy Loading) is the most common caching strategy.

Workflow

```
Application

↓

Redis

↓

Miss

↓

Database

↓

Redis

↓

Client
```

Advantages

- Simple
- Flexible
- Cache stores only frequently accessed data

Disadvantages

- First request is slower
- Cache consistency must be managed

---

# Q6. What is Read Through Cache?

### Answer

In Read Through caching, the cache itself loads data from the database.

```
Application

↓

Cache

↓

Database
```

Applications communicate only with the cache.

---

# Q7. What is Write Through Cache?

### Answer

Write Through writes data to Redis and the database simultaneously.

```
Application

↓

Redis

↓

Database
```

Advantages

- High consistency

Disadvantages

- Slightly slower writes

---

# Q8. What is Write Behind Cache?

### Answer

Write Behind stores data in Redis first.

Database updates happen asynchronously.

```
Application

↓

Redis

↓

Async Worker

↓

Database
```

Advantages

- Extremely fast writes

Disadvantages

- Risk of data loss if Redis fails before persistence

---

# Q9. What is Refresh Ahead Cache?

### Answer

Frequently accessed keys are refreshed before they expire.

```
TTL Near Expiry

↓

Background Refresh

↓

TTL Extended
```

This avoids cache misses for popular data.

---

# Q10. What is cache invalidation?

### Answer

Cache invalidation removes outdated data from Redis.

Example

```
Database Updated

↓

Delete Cache

↓

Next Read

↓

Fresh Data
```

Cache invalidation is often considered one of the hardest problems in distributed systems.

---

# Q11. Why is cache invalidation difficult?

### Answer

Applications may have

- Multiple cache servers
- Multiple application servers
- Replicas
- Concurrent writes

Keeping cached data synchronized with the database becomes challenging.

---

# Q12. What is TTL?

### Answer

TTL (Time To Live) defines how long a cache entry remains valid.

Example

```bash
SET product:101 "{}" EX 300
```

After 300 seconds

↓

Key expires automatically.

---

# Q13. Should every key have the same TTL?

### Answer

No.

Examples

| Data | Recommended TTL |
|------|-----------------|
| Product Catalog | 1 hour |
| User Profile | 15 minutes |
| OTP | 5 minutes |
| Session | 30 minutes |
| Feature Flags | Several hours |

TTL depends on business requirements.

---

# Q14. What is Cache Stampede?

### Answer

Many requests arrive after a popular key expires.

```
Key Expires

↓

1000 Requests

↓

Database Flood
```

Solutions

- Mutex locking
- Refresh Ahead
- Randomized TTL
- Background refresh

---

# Q15. What is Cache Avalanche?

### Answer

Many keys expire simultaneously.

```
Millions of Keys

↓

Expire Together

↓

Database Overloaded
```

Solution

Use randomized TTL values.

---

# Q16. What is Cache Penetration?

### Answer

Requests repeatedly ask for data that does not exist.

```
Redis

↓

Miss

↓

Database

↓

Not Found
```

Solutions

- Bloom Filters
- Negative Caching

---

# Q17. What is Negative Caching?

### Answer

Cache "not found" responses.

Example

```
User Not Found

↓

Store NULL

↓

TTL 60 seconds
```

Prevents repeated database lookups.

---

# Q18. What are Hot Keys?

### Answer

Hot Keys receive a massive number of requests.

```
Millions of Users

↓

One Key

↓

CPU Spike
```

Solutions

- Replication
- Local cache
- Sharding

---

# Q19. What is Cache Consistency?

### Answer

Cache consistency means Redis and the database contain the same logical data.

Common strategies

- Delete cache after database update
- Update cache immediately
- Short TTL

---

# Q20. Which cache pattern is most common?

### Answer

```
Cache Aside
```

It is simple, flexible, and widely used in production systems.

---

# Q21. What is cache warming?

### Answer

Frequently used data is loaded into Redis before traffic arrives.

```
Application Starts

↓

Preload Data

↓

Redis Ready
```

Commonly used after deployments.

---

# Q22. Should every database query be cached?

### Answer

No.

Avoid caching

- Frequently changing data
- One-time queries
- Highly personalized data (unless beneficial)
- Very large datasets

---

# Q23. How do you measure cache performance?

### Answer

Common metrics

- Cache Hit Ratio
- Cache Miss Ratio
- Response Time
- Memory Usage
- Evictions
- Latency

---

# Q24. What is a good Cache Hit Ratio?

### Answer

It depends on the workload.

Typical targets

| Application | Hit Ratio |
|-------------|-----------|
| General Web Apps | 80–90% |
| CDN | 95%+ |
| Read-heavy APIs | 90%+ |

---

# Q25. Why shouldn't Redis be the only database?

### Answer

Redis primarily stores data in memory.

Applications usually require

- Durable storage
- Complex queries
- Transactions
- Historical records

Redis complements databases rather than replacing them.

---

# Q26. What happens if Redis crashes?

### Answer

If Redis is unavailable

```
Application

↓

Database

↓

Response
```

The application should gracefully fall back to the database while Redis recovers.

---

# Q27. How do you prevent cache stampede in production?

### Answer

Common techniques

- Distributed locks
- Mutex
- Refresh Ahead
- Background refresh
- Randomized TTL
- Request coalescing

---

# Q28. Why use randomized TTL?

### Answer

Instead of

```
All Keys

↓

Expire

↓

10:00 AM
```

Use

```
300 sec

315 sec

287 sec

322 sec
```

This prevents simultaneous expiration.

---

# Q29. What are common Redis caching use cases?

### Answer

- Product catalog
- User sessions
- API responses
- Search results
- Dashboard statistics
- Configuration
- Authentication tokens
- Rate limiting
- Recommendation results

---

# Q30. Design a caching architecture for an e-commerce application.

### Answer

```
Client

↓

Load Balancer

↓

Application

↓

Redis

↓

PostgreSQL
```

Cached data

- Products
- Categories
- Inventory
- Search results
- User sessions

Database stores

- Orders
- Payments
- Transactions
- Permanent records

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Most common cache strategy? | Cache Aside |
| Prevent cache avalanche? | Randomized TTL |
| Prevent cache penetration? | Bloom Filter |
| Prevent cache stampede? | Distributed Lock |
| Expire keys automatically? | TTL |
| Cache not-found responses? | Negative Caching |
| Best cache for Redis? | In-memory |

---

# Senior Interview Tips

Interviewers often ask:

> If your cache hit ratio suddenly drops from 95% to 30%, what would you investigate?

A strong answer includes:

- Recent deployments
- TTL configuration
- Cache evictions
- Redis memory usage
- Database latency
- Network issues
- Cache invalidation logic
- Hot keys
- Monitoring dashboards

This demonstrates systematic production troubleshooting rather than guessing.

---

# Common Mistakes

## Caching Everything

Not every query benefits from caching.

---

## Using One TTL for Every Key

Different data has different freshness requirements.

---

## Ignoring Cache Invalidation

Stale cache can cause incorrect application behavior.

---

## No Database Fallback

Applications should continue functioning even if Redis becomes unavailable.

---

# Best Practices

- Choose the appropriate caching pattern for the workload.
- Configure TTL values based on business requirements.
- Monitor cache hit ratio and eviction rates.
- Use randomized TTL to prevent cache avalanches.
- Protect against cache stampedes with locking or refresh strategies.
- Implement graceful fallback to the database.
- Regularly review caching effectiveness and remove unnecessary cached data.

---

# Summary

Redis caching significantly improves application performance and scalability by reducing database load and serving frequently accessed data from memory. Understanding cache patterns, invalidation strategies, TTL management, and common failure scenarios is essential for designing reliable, high-performance backend systems. Senior interviews focus not only on concepts but also on production trade-offs and operational considerations.

---

# Key Takeaways

- Redis is one of the most widely used caching technologies due to its speed and flexibility.
- Cache Aside is the most common caching strategy in production.
- TTLs, cache invalidation, and consistency are fundamental to reliable caching.
- Cache Stampede, Avalanche, and Penetration are common production problems with well-established mitigation strategies.
- Monitor cache hit ratio, latency, and memory usage to evaluate cache effectiveness.
- Always design applications to function correctly even when the cache is unavailable.
- Strong interview answers combine concepts, architecture, trade-offs, and real-world production examples.