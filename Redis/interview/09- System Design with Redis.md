# System Design with Redis

## Overview

Redis is one of the most widely used technologies in System Design interviews.

Unlike SQL databases that serve as the **source of truth**, Redis is usually introduced to solve problems related to:

- Low latency
- High throughput
- Scalability
- Distributed coordination
- Session management
- Rate limiting
- Messaging
- Leaderboards
- Caching

Senior Backend interviews rarely ask,

> "What is Redis?"

Instead, they ask

> "Where would you use Redis in this architecture?"

or

> "Why did you choose Redis instead of PostgreSQL?"

This chapter covers common Redis System Design interview questions along with architecture diagrams, design decisions, trade-offs, and production considerations.

---

# Q1. Where does Redis fit into a typical system architecture?

### Answer

Redis usually sits between the application and the primary database.

Architecture

```
                Client

                   │

                   ▼

            Load Balancer

                   │

                   ▼

          Application Servers

              │         │

      Cache Hit      Cache Miss

              │         │

              ▼         ▼

            Redis   PostgreSQL

                       │

                       ▼

                  Persistent Data
```

Redis reduces database load by serving frequently requested data directly from memory.

---

# Q2. Design a high-performance product catalog.

### Answer

Product catalogs are read-heavy.

Typical workflow

```
Client

↓

Application

↓

Redis

↓

Product Found

↓

Response
```

Cache Miss

```
Application

↓

Database

↓

Redis

↓

Response
```

Cached data

- Product details
- Categories
- Reviews
- Inventory summary

Benefits

- Low latency
- Reduced database load
- Higher throughput

---

# Q3. Design a user session management system.

### Answer

Redis is commonly used for session storage.

Architecture

```
User Login

↓

Application

↓

Redis

↓

Session Token

↓

TTL
```

Session

```
session:abc123

↓

User ID

↓

Expiration
```

Advantages

- Automatic expiration
- Fast lookup
- Shared across servers

---

# Q4. Design a distributed rate limiter.

### Answer

Redis counters make rate limiting simple.

Workflow

```
Request

↓

INCR

↓

Count

↓

Exceeded?

↓

Reject
```

Example

```text
INCR api:user:101

EXPIRE api:user:101 60
```

If count exceeds the limit,

return

```
HTTP 429
```

---

# Q5. Why is Redis preferred for rate limiting?

### Answer

Redis provides

- Atomic counters
- TTL
- Fast operations
- Shared state across multiple application servers

Databases are generally too slow for this workload.

---

# Q6. Design a leaderboard.

### Answer

Use

```
Sorted Sets
```

Architecture

```
Player

↓

Score

↓

Sorted Set

↓

Top 100
```

Example

```bash
ZADD leaderboard 900 Alice

ZADD leaderboard 850 Bob
```

Retrieve top players

```bash
ZREVRANGE leaderboard 0 99
```

---

# Q7. Design a shopping cart.

### Answer

Architecture

```
Client

↓

Application

↓

Redis

↓

Shopping Cart
```

Each user has

```
cart:user:101
```

Store

- Product IDs
- Quantity
- Timestamp

TTL may be applied to remove abandoned carts.

---

# Q8. Design an API response cache.

### Answer

Workflow

```
Request

↓

Redis

↓

Hit?

↓

Return

↓

Else

↓

Database

↓

Cache

↓

Response
```

Typical TTL

- 5 minutes
- 15 minutes
- 1 hour

depending on data freshness.

---

# Q9. Design a notification system.

### Answer

Redis Pub/Sub

```
Publisher

↓

Channel

↓

Subscribers
```

Example

```
Order Service

↓

notifications

↓

Email Service

↓

SMS Service
```

Suitable for real-time messaging where message durability is not required.

---

# Q10. When should Redis Streams be used instead of Pub/Sub?

### Answer

Use Streams when

- Messages must be persisted
- Consumers may be offline
- Replay is required
- Consumer groups are needed

Comparison

| Pub/Sub | Streams |
|----------|----------|
| Fire-and-forget | Persistent |
| No replay | Replay supported |
| No consumer groups | Consumer groups |
| Best effort delivery | Reliable processing |

---

# Q11. Design a real-time analytics dashboard.

### Answer

Architecture

```
Application

↓

Redis

↓

Counters

↓

Dashboard
```

Examples

- Active users
- Page views
- Orders
- Revenue
- API requests

Use

```
INCR

HINCRBY

Sorted Sets
```

---

# Q12. Design a distributed lock.

### Answer

Workflow

```
Application A

↓

SET lock NX EX

↓

Lock Acquired
```

Other applications

```
Lock Exists

↓

Retry
```

Example

```bash
SET order_lock value NX EX 30
```

---

# Q13. Why are distributed locks required?

### Answer

Prevent multiple servers from processing the same resource simultaneously.

Example

```
Two Payment Workers

↓

Same Payment

↓

Double Charge
```

Redis lock

↓

Only one worker proceeds.

---

# Q14. Design a background job queue.

### Answer

Architecture

```
Producer

↓

Redis Stream

↓

Consumer Group

↓

Workers
```

Workers process jobs independently.

Examples

- Emails
- Image processing
- Report generation

---

# Q15. Design an authentication system.

### Answer

Workflow

```
Login

↓

JWT

↓

Redis

↓

Blacklist

↓

Logout
```

Redis stores

- Refresh tokens
- Session state
- Revoked tokens
- Login attempts

---

# Q16. Design a feature flag system.

### Answer

Architecture

```
Application

↓

Redis

↓

Feature Flags

↓

Decision
```

Advantages

- Instant updates
- Low latency
- No database queries

---

# Q17. Design a URL shortener.

### Answer

Redis stores

```
short-url

↓

original-url
```

Example

```
abc123

↓

https://example.com/product/101
```

Frequently accessed URLs are served directly from Redis.

---

# Q18. Design a recommendation cache.

### Answer

```
User

↓

Redis

↓

Recommended Products
```

Instead of computing recommendations repeatedly,

cache them with a TTL.

---

# Q19. How would you cache database queries?

### Answer

Use the Cache Aside pattern.

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

Most common production strategy.

---

# Q20. Design a scalable Redis architecture for an e-commerce platform.

### Answer

```
                    Internet

                        │

                        ▼

                Load Balancer

                        │

                        ▼

              Application Layer

         ┌──────────┼──────────┐

         ▼          ▼          ▼

     Service A   Service B   Service C

                 │

                 ▼

             Redis Cluster

      ┌────────┼────────┐

      ▼        ▼        ▼

   Primary   Primary   Primary

      │         │         │

      ▼         ▼         ▼

   Replica   Replica   Replica

                 │

                 ▼

           PostgreSQL Cluster
```

Redis responsibilities

- Sessions
- Product cache
- Shopping carts
- Rate limiting
- Leaderboards
- Recommendations
- Inventory cache

Database responsibilities

- Orders
- Payments
- Customer data
- Permanent records

---

# Q21. What should never be stored only in Redis?

### Answer

Critical business data.

Examples

- Orders
- Payments
- Bank transactions
- Audit logs

Redis is often a performance layer, not the primary system of record.

---

# Q22. How do you decide whether data should be cached?

### Answer

Questions to ask

- Is it read frequently?
- Does it change rarely?
- Is it expensive to compute?
- Can stale data be tolerated?

If the answer is mostly yes,

Redis is a strong candidate.

---

# Q23. What are common Redis bottlenecks in System Design?

### Answer

- Hot Keys
- Large values
- Memory limits
- Replication lag
- Poor eviction policy
- Network latency
- Inefficient key design

---

# Q24. When should Redis Cluster be used?

### Answer

Use Redis Cluster when

- Dataset exceeds one server's memory
- Higher write throughput is needed
- Horizontal scaling is required
- High availability is required

---

# Q25. What are common System Design interview mistakes?

### Answer

Candidates often

- Use Redis as the primary database.
- Ignore cache invalidation.
- Forget TTL.
- Ignore replication lag.
- Confuse Sentinel with Cluster.
- Skip monitoring and backups.

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Best cache? | Redis |
| Session storage? | Redis |
| Leaderboards? | Sorted Sets |
| Rate limiting? | INCR + EXPIRE |
| Distributed lock? | SET NX EX |
| Job queue? | Streams |
| Notifications? | Pub/Sub |
| Large-scale caching? | Redis Cluster |

---

# Senior Interview Tips

Interviewers usually evaluate **design decisions**, not Redis syntax.

When answering System Design questions

Always explain

1. Why Redis is needed.
2. Why another database isn't sufficient.
3. Trade-offs.
4. Failure handling.
5. Monitoring.
6. Scaling strategy.
7. Data consistency.

Strong candidates explain **why** Redis is chosen rather than simply saying "use Redis."

---

# Common Mistakes

## Using Redis for Permanent Business Data

Redis should rarely be the only storage layer for critical data.

---

## Ignoring Cache Invalidation

Incorrect invalidation strategies lead to stale or inconsistent data.

---

## Forgetting High Availability

Production Redis deployments should include replication, failover, and monitoring.

---

## Overusing Redis

Not every piece of data benefits from caching.

Analyze access patterns before introducing Redis.

---

# Best Practices

- Cache only data that provides measurable performance benefits.
- Design TTL values based on business requirements.
- Combine Redis with durable databases.
- Use Redis Cluster for large-scale deployments.
- Monitor hit ratio, latency, memory usage, and failover events.
- Test disaster recovery and failover procedures regularly.
- Keep the architecture simple and avoid unnecessary complexity.

---

# Summary

Redis is a foundational technology in modern System Design because it enables high-performance caching, session management, rate limiting, distributed locking, messaging, and real-time analytics. Senior backend engineers should understand not only how to use Redis, but also where it fits within a larger distributed architecture, the trade-offs involved, and the operational considerations required for production systems.

---

# Key Takeaways

- Redis is typically a performance layer rather than the primary data store.
- Cache Aside is the most common production caching strategy.
- Sorted Sets power leaderboards and ranking systems.
- Streams provide reliable messaging, while Pub/Sub is best for real-time notifications.
- Redis enables distributed locking, rate limiting, and session management with minimal latency.
- System Design interviews emphasize architectural decisions, scalability, fault tolerance, and trade-offs over command syntax.
- Always justify why Redis is the right tool for the problem being solved.