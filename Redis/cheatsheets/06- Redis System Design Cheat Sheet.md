# Redis System Design Cheat Sheet

## Overview

Redis is rarely used as a standalone database in large-scale systems. Instead, it is commonly integrated into distributed architectures to improve performance, scalability, reliability, and user experience.

This cheat sheet summarizes common system design patterns involving Redis, when to use them, and key architectural considerations.

---

# Where Redis Fits

```text
                  Users
                     │
                     ▼
              Load Balancer
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
     API Server              API Server
        │                         │
        ├──────────────┐──────────┤
        ▼              ▼
      Redis       Database
        │
        ▼
 Background Workers
```

---

# Common Redis Use Cases

| Use Case | Redis Feature |
|----------|---------------|
| API Cache | Strings |
| Session Store | Strings |
| User Profile Cache | Hashes |
| Shopping Cart | Hashes |
| Job Queue | Lists / Streams |
| Leaderboards | Sorted Sets |
| Rate Limiting | Strings + Expiration |
| Notifications | Pub/Sub |
| Event Processing | Streams |
| Distributed Locking | SET NX EX |
| Real-time Analytics | HyperLogLog, Bitmaps |
| Location Services | Geospatial |

---

# Cache-Aside Pattern

## Architecture

```text
        Request
           │
           ▼
     Check Redis
      │        │
 Hit  │        │ Miss
      ▼        ▼
 Return     Database
               │
               ▼
        Store in Redis
               │
               ▼
           Return
```

---

## Advantages

- Simple
- Widely adopted
- Database protected
- Easy to implement

---

## Disadvantages

- Cache misses
- Stale data possible
- Application manages cache

---

# Read-Through Cache

```text
Application

↓

Redis

↓

Database
```

Redis automatically loads missing data.

Best for

- Managed cache providers
- Transparent caching

---

# Write-Through Cache

```text
Application

↓

Redis

↓

Database
```

Every write updates both cache and database.

Advantages

- Strong consistency
- Cache always fresh

Disadvantages

- Higher write latency

---

# Write-Behind (Write-Back)

```text
Application

↓

Redis

↓

Return Success

↓

Background Worker

↓

Database
```

Advantages

- Very fast writes
- High throughput

Disadvantages

- Risk of data loss if Redis fails before persistence

---

# Session Management

```text
Client

↓

API

↓

Redis Session

↓

Authentication
```

Typical key

```
session:user:101
```

TTL

```
30 minutes
```

Benefits

- Stateless application servers
- Easy horizontal scaling
- Fast authentication

---

# API Response Caching

```text
Client

↓

API

↓

Redis

↓

Database
```

Typical key

```
cache:products:page:1
```

TTL

```
5 minutes
```

---

# Leaderboard Design

```text
Player Score

↓

Sorted Set

↓

Ranking

↓

Top 100
```

Commands

```bash
ZADD

ZINCRBY

ZREVRANGE
```

---

# Rate Limiting

Simple implementation

```text
User Request

↓

INCR

↓

EXPIRE

↓

Limit?
```

Example

```bash
INCR rate:user:101

EXPIRE rate:user:101 60
```

---

# Distributed Lock

Acquire lock

```bash
SET order:lock unique-id NX EX 30
```

Release lock

Only if the lock owner matches the unique identifier (typically using a Lua script).

Use cases

- Scheduled jobs
- Inventory updates
- Payment processing

---

# Pub/Sub Architecture

```text
Publisher

↓

Redis Channel

↓

Subscriber A

↓

Subscriber B

↓

Subscriber C
```

Best for

- Notifications
- Live dashboards
- Chat systems

Not suitable when message durability is required.

---

# Stream Processing

```text
Producer

↓

Redis Stream

↓

Consumer Group

↓

Worker 1

Worker 2

Worker 3
```

Best for

- Order processing
- Email queues
- Background jobs
- Event-driven systems

---

# Distributed Queue

```text
API

↓

Redis Stream

↓

Workers

↓

Database
```

Benefits

- Reliable processing
- Consumer groups
- Message acknowledgment
- Replay capability

---

# Cache Invalidation

Strategies

| Strategy | Description |
|----------|-------------|
| TTL | Automatic expiration |
| Manual Delete | Remove cache after updates |
| Event-Based | Invalidate via messaging |
| Versioned Keys | Generate new cache keys |

---

# Cache Stampede Prevention

Problem

```text
Cache Expires

↓

Thousands of Requests

↓

Database Overloaded
```

Solutions

- Randomized TTL
- Distributed locking
- Background refresh
- Stale-while-revalidate

---

# Cache Penetration

Problem

```text
Invalid Key

↓

Redis Miss

↓

Database

↓

Redis Miss

↓

Database
```

Solutions

- Cache null values
- Bloom filters
- Request validation

---

# Cache Avalanche

Problem

```text
Millions of Keys

↓

Expire Together

↓

Database Flood
```

Solutions

- Random TTL values
- Warm-up cache
- Stagger expirations

---

# Hot Key Problem

```text
Popular Key

↓

Millions of Reads

↓

Redis CPU Spike
```

Solutions

- Local cache
- Replication
- Key sharding
- CDN

---

# Sharding Strategy

```text
User ID

↓

Hash Function

↓

Redis Node
```

Example

```
User 101

↓

Hash

↓

Node 2
```

Redis Cluster automatically performs this using 16,384 hash slots.

---

# High Availability Design

```text
              Sentinel

                 │

        ┌────────┴────────┐

        ▼                 ▼

     Master          Replica

                         │

                         ▼

                     Replica
```

Benefits

- Automatic failover
- Monitoring
- Service discovery

---

# Large-Scale Architecture

```text
                  Internet

                      │

                Load Balancer

                      │

          ┌───────────┴───────────┐

          ▼                       ▼

      API Server             API Server

          │                       │

          ├──────────────┬────────┤

          ▼              ▼

      Redis Cluster   Database

          │

          ▼

   Background Workers

          │

          ▼

     External Services
```

---

# System Design Decision Matrix

| Requirement | Redis Solution |
|------------|----------------|
| Fast Reads | Cache |
| User Sessions | Strings |
| User Profiles | Hashes |
| Queue | Streams |
| Messaging | Pub/Sub |
| Ranking | Sorted Sets |
| Location Search | Geospatial |
| Unique Counting | HyperLogLog |
| Feature Flags | Bitmaps |
| Distributed Lock | SET NX EX |

---

# Scaling Checklist

- Use connection pooling.
- Use pipelining for batch operations.
- Configure TTLs for cached data.
- Avoid large keys.
- Monitor hot keys.
- Add replicas for read-heavy workloads.
- Use Redis Cluster for horizontal scaling.
- Benchmark before major changes.

---

# Common System Design Interview Questions

| Question | Expected Discussion |
|----------|---------------------|
| Design a URL shortener | Cache lookups, counters, TTL |
| Design a rate limiter | INCR + EXPIRE, sliding window |
| Design a leaderboard | Sorted Sets |
| Design a chat application | Pub/Sub or Streams |
| Design a notification system | Pub/Sub + Streams |
| Design a session store | Strings with TTL |
| Design an API cache | Cache-Aside pattern |
| Design an order processing system | Streams + Consumer Groups |
| Design a distributed lock | SET NX EX + Lua unlock |
| Design a real-time analytics platform | HyperLogLog, Bitmaps, Streams |

---

# Senior System Design Tips

- Choose the appropriate Redis data structure based on access patterns.
- Design for cache failures—never assume Redis is always available.
- Combine Redis with a durable database for business-critical data.
- Prefer Redis Streams over Pub/Sub when message durability and replay are required.
- Monitor cache hit ratio, latency, memory usage, and hot keys.
- Plan for scaling from a single instance to Sentinel or Cluster as traffic grows.
- Understand common caching failure scenarios (stampede, penetration, avalanche) and their mitigation techniques.

---

# 60-Second Revision

```text
Redis

↓

Cache

↓

Sessions

↓

Rate Limiting

↓

Distributed Locks

↓

Leaderboards

↓

Queues

↓

Streams

↓

Pub/Sub

↓

High Availability

↓

Sentinel

↓

Cluster

↓

Performance

↓

TTL

Pipeline

Connection Pool

SCAN

Monitor

↓

Production Ready
```