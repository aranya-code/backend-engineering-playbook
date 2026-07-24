# Real World Caching Examples

## Overview

Learning individual caching patterns is important, but production systems rarely rely on a single strategy.

Large technology companies combine multiple caching techniques based on:

- Data volatility
- Read/write ratio
- Business requirements
- Consistency needs
- Latency requirements
- Failure tolerance

This chapter explores how Redis is used in real-world backend systems and how different caching patterns work together.

---

# Example 1 — E-Commerce Platform

Consider an online shopping application.

```
                Client

                   │

                   ▼

             Load Balancer

                   │

                   ▼

            Backend Services

      ┌─────────┼─────────┐

      ▼         ▼         ▼

 Product   Inventory   Orders

      │         │         │

      ▼         ▼         ▼

             Redis Cache

                   │

                   ▼

              PostgreSQL
```

---

## What Should Be Cached?

| Data | Cache? | Why |
|-------|---------|-----|
| Product Details | ✅ Yes | Frequently read |
| Categories | ✅ Yes | Rarely change |
| Product Images | ❌ CDN | Better served by CDN |
| Inventory | ⚠ Short TTL | Frequently updated |
| Orders | ❌ Usually No | Strong consistency required |
| User Cart | ✅ Yes | Fast access |
| Recommendations | ✅ Yes | Expensive to generate |

---

## Product Details

Pattern:

```
Cache Aside
```

Flow

```
Client

↓

Redis

↓

Hit?

↓

Return Product

↓

Else Database

↓

Populate Redis
```

TTL

```
30 Minutes
```

---

## Inventory

Inventory changes frequently.

Pattern

```
Write Through

or

Event-Based Invalidation
```

```
Inventory Updated

↓

Database

↓

Redis Updated

↓

Users
```

---

## Shopping Cart

Shopping carts are excellent Redis candidates.

```
User

↓

Redis

↓

Shopping Cart
```

Advantages

- Fast
- Temporary
- Session-based

Typical TTL

```
24 Hours
```

---

## Product Search

Search results are expensive.

```
Redis

↓

Search Results

↓

TTL

5 Minutes
```

Frequently repeated searches avoid Elasticsearch or SQL.

---

# Example 2 — Banking Application

Banking systems prioritize consistency over performance.

```
ATM

↓

API

↓

Database

↓

Redis
```

---

## Account Balance

Pattern

```
Write Through
```

```
Transfer

↓

Database

↓

Redis

↓

Client
```

Strong consistency required.

---

## Exchange Rates

Pattern

```
Refresh Ahead
```

```
Every Minute

↓

Worker

↓

Redis
```

Users always receive fresh values.

---

## Transaction History

Usually

```
Database

↓

Cache Aside
```

Short TTL

```
30 Seconds
```

---

# Example 3 — Social Media Platform

```
Users

↓

Feed Service

↓

Redis

↓

Database
```

---

## News Feed

Pattern

```
Cache Aside
```

```
User Opens Feed

↓

Redis

↓

Miss?

↓

Database

↓

Redis
```

---

## Trending Topics

```
Refresh Ahead
```

Worker refreshes every minute.

---

## User Profiles

```
Cache Aside
```

TTL

```
15 Minutes
```

---

## Like Count

```
Write Behind
```

```
Like

↓

Redis

↓

Queue

↓

Database
```

Thousands of writes become batched updates.

---

# Example 4 — Video Streaming Platform

```
User

↓

CDN

↓

Redis

↓

Metadata Database
```

---

## Video Metadata

Pattern

```
Cache Aside
```

TTL

```
1 Hour
```

---

## Trending Videos

```
Refresh Ahead
```

Always warm.

---

## Recommendations

Generated using ML.

```
Redis

↓

Recommendation List

↓

TTL

10 Minutes
```

---

# Example 5 — AI / LLM Platform

```
User

↓

API Gateway

↓

LLM Service

↓

Redis

↓

Vector DB
```

---

## Prompt Cache

Many prompts repeat.

```
Prompt

↓

Redis

↓

Cached Response
```

Benefits

- Lower LLM cost
- Faster responses

---

## Embeddings

```
Text

↓

Embedding

↓

Redis
```

Avoid repeated embedding generation.

---

## Rate Limiting

```
API Key

↓

Redis

↓

Token Bucket
```

---

## Conversation Context

```
User

↓

Redis

↓

Conversation State
```

Short TTL

```
30 Minutes
```

---

# Example 6 — Authentication System

```
User

↓

Login

↓

Redis

↓

Database
```

---

## Sessions

Store

```
Session Token

↓

Redis
```

TTL

```
30 Minutes
```

---

## OTP

```
Phone

↓

OTP

↓

Redis

↓

TTL

5 Minutes
```

---

## Failed Login Attempts

```
Redis Counter

↓

5 Attempts

↓

Blocked
```

Rate limiting protects against brute-force attacks.

---

# Example 7 — API Gateway

```
Internet

↓

Nginx

↓

Redis

↓

Backend
```

Redis stores

- Rate limits
- JWT blacklist
- API keys
- Usage counters

---

# Example 8 — CMS Platform

```
Editors

↓

Database

↓

Redis

↓

Visitors
```

---

## Articles

```
Cache Aside

TTL

30 Minutes
```

---

## Homepage

```
Refresh Ahead
```

Always cached.

---

# Example 9 — Gaming Platform

```
Players

↓

Redis

↓

Game Servers
```

---

## Leaderboards

Redis Sorted Sets

```
ZSET
```

Fast ranking.

---

## Matchmaking

Redis

```
SET

LIST

STREAM
```

---

## Online Players

```
SET

↓

Player IDs
```

---

# Example 10 — Analytics Platform

```
Applications

↓

Redis

↓

Kafka

↓

Warehouse
```

---

## Page Views

Pattern

```
Write Behind
```

```
Redis Counter

↓

Worker

↓

Database
```

Millions of writes become batched.

---

## Dashboard

```
Refresh Ahead
```

Updated every minute.

---

# Example 11 — IoT Platform

Millions of sensors continuously send data.

```
Sensors

↓

Redis

↓

Kafka

↓

Database
```

---

## Device State

```
Redis

↓

Latest Reading
```

---

## Historical Data

Stored directly in

- ClickHouse
- TimescaleDB
- InfluxDB

Redis only stores the latest values.

---

# Example 12 — SaaS Platform

```
Tenant

↓

API

↓

Redis
```

---

Cached data

- Tenant configuration
- Permissions
- Feature flags
- User sessions

---

# Choosing the Right Caching Pattern

| Use Case | Pattern |
|----------|----------|
| Product Details | Cache Aside |
| Inventory | Write Through |
| Analytics | Write Behind |
| Homepage | Refresh Ahead |
| Sessions | Direct Redis Storage |
| OTP | TTL Cache |
| Exchange Rates | Refresh Ahead |
| Search Results | Cache Aside |
| Recommendations | Cache Aside |
| Trending Content | Refresh Ahead |
| Rate Limiting | Token Bucket |
| Leaderboards | Sorted Sets |
| Counters | Write Behind |

---

# Recommended TTLs

| Data | TTL |
|------|------|
| Product Details | 30–60 Minutes |
| Categories | 12–24 Hours |
| Sessions | 30 Minutes |
| OTP | 5 Minutes |
| JWT Blacklist | Token Expiration |
| Exchange Rates | 1 Minute |
| Dashboard | 30–60 Seconds |
| Search Results | 5–10 Minutes |
| User Profiles | 15–30 Minutes |
| Feature Flags | 5–30 Minutes |
| Shopping Cart | 24 Hours |

---

# Cache Layer Architecture

```
                     Client

                        │

                        ▼

                  Browser Cache

                        │

                        ▼

                      CDN

                        │

                        ▼

               API Gateway Cache

                        │

                        ▼

             Application Memory Cache

                        │

                        ▼

                     Redis

                        │

                        ▼

                    Database
```

Each layer removes load from the next.

---

# Production Architecture

```
                     Internet

                         │

                    Load Balancer

                         │

                 Kubernetes Cluster

                         │

          ┌──────────────┼──────────────┐

          ▼              ▼              ▼

     Backend A      Backend B      Backend C

          │              │              │

          └──────────────┼──────────────┘

                         ▼

                  Redis Cluster

             ┌──────┼────────┐

             ▼      ▼        ▼

          Primary Replica Replica

                         │

                         ▼

                 PostgreSQL Cluster
```

---

# Common Production Mistakes

## Caching Everything

Not all data benefits from caching.

Avoid caching:

- Highly volatile data
- Sensitive information
- One-time queries
- Large binary files

---

## Very Long TTL

```
24 Hours
```

May result in stale data.

Choose TTLs based on business requirements.

---

## Ignoring Cache Failures

Applications should continue functioning if Redis becomes unavailable.

Always implement graceful degradation.

---

## Using Redis as Primary Database

Redis should generally act as:

```
Performance Layer
```

not the primary source of truth.

---

## No Monitoring

Monitor:

- Hit ratio
- Miss ratio
- Evictions
- Memory usage
- Hot keys
- Latency
- Replication lag
- Connection count

---

# Best Practices

- Cache only data that provides measurable performance improvements.
- Choose caching patterns based on consistency requirements rather than convenience.
- Use Cache Aside for most read-heavy workloads.
- Use Write Through for critical transactional data.
- Use Write Behind only when eventual consistency is acceptable.
- Refresh hot data proactively using Refresh Ahead.
- Apply TTL jitter to avoid cache avalanches.
- Combine browser caching, CDNs, application caches, and Redis for maximum scalability.
- Continuously monitor cache effectiveness and adjust TTLs based on production traffic.

---

# Performance Considerations

| Component | Benefit |
|-----------|----------|
| Browser Cache | Eliminates network requests |
| CDN | Global low-latency delivery |
| Application Cache | Reduces Redis traffic |
| Redis | Sub-millisecond data access |
| Database | Persistent source of truth |

A layered caching strategy significantly reduces latency and backend load while improving resilience.

---

# Production Considerations

For production systems:

- Design caching strategies per data type instead of applying a single approach universally.
- Ensure Redis failures do not bring down the application—implement graceful fallbacks.
- Use Redis Cluster with replication for high availability and horizontal scalability.
- Apply cache invalidation carefully to maintain consistency.
- Use monitoring dashboards to track hit ratio, latency, memory usage, and hot keys.
- Load test caching behavior under peak traffic, deployments, and failover scenarios.
- Regularly review cache effectiveness and remove entries that provide little performance benefit.

---

# Summary

Real-world systems rarely rely on a single caching strategy. Instead, they combine techniques such as Cache Aside, Write Through, Write Behind, Refresh Ahead, TTL-based caching, rate limiting, and multi-level caching based on workload characteristics. Redis serves as a high-performance caching layer that complements persistent databases, enabling applications to scale while maintaining acceptable consistency. The most successful production architectures tailor caching strategies to specific data types, monitor cache performance continuously, and design for graceful degradation during failures.

---

# Key Takeaways

- Different data types require different caching strategies.
- Cache Aside is the default choice for most read-heavy applications.
- Write Through is suitable for strongly consistent workloads.
- Write Behind is ideal for high-volume asynchronous writes.
- Refresh Ahead keeps frequently accessed data continuously available.
- Redis is commonly used for sessions, OTPs, rate limiting, leaderboards, and AI prompt caching.
- Multi-level caching (Browser → CDN → Application → Redis → Database) provides the best scalability.
- Effective monitoring, TTL tuning, and graceful degradation are essential for production-ready caching systems.