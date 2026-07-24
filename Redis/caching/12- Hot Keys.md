# Hot Keys

## Overview

A **Hot Key** is a Redis key that receives **a disproportionately large number of requests compared to other keys**.

In a distributed Redis deployment, millions of keys may exist, but only a handful receive the majority of traffic.

For example:

- Homepage cache
- Trending products
- Popular videos
- User session of a celebrity
- Global configuration
- Feature flags
- Exchange rates

Because Redis Cluster partitions data based on the key hash, a hot key can overload a **single Redis node**, creating a bottleneck while the rest of the cluster remains mostly idle.

Hot keys are one of the most common scalability problems in high-traffic systems.

---

# What is a Hot Key?

Imagine an e-commerce application.

```
Products

↓

Product 1

10 Requests

Product 2

15 Requests

Product 3

8 Requests

Product 999

2,000,000 Requests
```

Product **999** is a hot key.

---

# Normal Traffic Distribution

```
Redis Cluster

┌──────────────┐
│ Node A       │
│ 30% Traffic  │
└──────────────┘

┌──────────────┐
│ Node B       │
│ 35% Traffic  │
└──────────────┘

┌──────────────┐
│ Node C       │
│ 35% Traffic  │
└──────────────┘
```

Traffic is balanced.

---

# Hot Key Scenario

```
Redis Cluster

┌──────────────┐
│ Node A       │
│ 95% Traffic  │
└──────────────┘

┌──────────────┐
│ Node B       │
│ 3% Traffic   │
└──────────────┘

┌──────────────┐
│ Node C       │
│ 2% Traffic   │
└──────────────┘
```

Only one node becomes overloaded.

---

# Why Hot Keys Occur

Common reasons include:

- Viral content
- Flash sales
- Trending products
- Login sessions
- Global configuration
- Popular search results
- Frequently accessed dashboards
- Shared application settings

---

# Real Production Example

Suppose Amazon starts a flash sale.

```
iPhone 18

↓

Homepage

↓

Millions of Users

↓

Redis Key

↓

product:iphone18
```

Every request targets the same key.

---

# Symptoms

Common production symptoms:

- One Redis node reaches 100% CPU
- Increased response latency
- Network saturation
- Connection pool exhaustion
- Timeout exceptions
- Reduced throughput
- Uneven cluster utilization

---

# Detecting Hot Keys

Useful Redis commands

```
redis-cli --hotkeys
```

Requires:

```
maxmemory-policy

LFU
```

Redis identifies frequently accessed keys.

---

Other useful metrics

```
INFO commandstats

INFO stats

MONITOR
```

Application metrics

- Requests per key
- Latency per key
- Redis CPU
- Network bandwidth

---

# Why Hot Keys are Dangerous

Suppose

```
Homepage

↓

10 Million Requests

↓

Single Redis Node
```

Even though Redis is fast:

```
CPU

↓

100%

↓

Latency

↓

Timeouts
```

Users experience slower responses.

---

# Hot Key Architecture

```
                Client Requests

        ┌──────────┼──────────┐

        ▼          ▼          ▼

    Same Redis Key

             │

             ▼

      Single Redis Node

             │

             ▼

        Performance Bottleneck
```

---

# Solution 1 — Local Application Cache

Instead of every request reaching Redis

```
Client

↓

Application

↓

Redis
```

Store frequently accessed data locally.

```
Client

↓

Application Cache

↓

Redis
```

Examples

- Caffeine (Java)
- Guava Cache
- Python in-memory cache
- Django local-memory cache

---

# Local Cache Architecture

```
Client

↓

Application

↓

Local Cache

↓

Redis

↓

Database
```

Redis traffic drops significantly.

---

# Solution 2 — Replication

Instead of

```
Primary Redis

↓

All Reads
```

Use replicas

```
Primary

↓

Replica A

Replica B

Replica C
```

Read traffic is distributed.

---

# Solution 3 — Key Sharding

Instead of

```
product:999
```

Split

```
product:999:1

product:999:2

product:999:3

product:999:4
```

Application randomly selects one.

Traffic spreads across multiple nodes.

---

# Key Sharding Example

```
Users

↓

Hash Function

↓

Replica 1

Replica 2

Replica 3

Replica 4
```

Each replica serves part of the requests.

---

# Solution 4 — CDN

For static content

```
Users

↓

CDN

↓

Redis

↓

Database
```

Redis traffic decreases dramatically.

---

# Solution 5 — Multi-Level Cache

```
Browser Cache

↓

CDN

↓

Application Cache

↓

Redis

↓

Database
```

Each layer absorbs part of the load.

---

# Solution 6 — Request Coalescing

Suppose

```
1000 Requests

↓

Same Key
```

Instead

```
1000 Requests

↓

One Redis Read

↓

1000 Responses
```

Duplicate work is eliminated.

---

# Solution 7 — Load Balancing Reads

```
Application

↓

Redis Replica

↓

Redis Replica

↓

Redis Replica
```

Distributes read traffic.

---

# Solution 8 — Cache Warming

Popular keys are loaded before traffic arrives.

```
Deployment

↓

Worker

↓

Redis

↓

Users
```

Prevents sudden spikes after deployment.

---

# Solution 9 — Rate Limiting

```
Client

↓

API Gateway

↓

100 Requests/Second

↓

Redis
```

Protects Redis against abuse.

---

# Hot Key vs Cache Stampede

| Feature | Hot Key | Cache Stampede |
|----------|----------|----------------|
| Cause | High Traffic | Expired Key |
| Cache Exists | Yes | No |
| Database Load | Low | Very High |
| Redis Load | Very High | Low Initially |
| Solution | Replication | Distributed Lock |

---

# Hot Key vs Cache Avalanche

| Feature | Hot Key | Cache Avalanche |
|----------|----------|-----------------|
| Number of Keys | One/Few | Thousands |
| Redis Load | High | Low |
| Database Load | Usually Low | Extremely High |
| Cause | Traffic | Mass Expiration |

---

# Hot Key vs Cache Penetration

| Feature | Hot Key | Cache Penetration |
|----------|----------|-------------------|
| Key Exists | Yes | No |
| Redis Hit Ratio | High | Low |
| Database Traffic | Low | High |
| Main Issue | Redis Bottleneck | Database Bottleneck |

---

# Real-World Examples

## Flash Sale

```
Black Friday

↓

One Product

↓

Millions of Reads

↓

Hot Key
```

---

## Social Media

```
Celebrity Profile

↓

Millions of Visits

↓

Same Cache Key
```

---

## Cryptocurrency

```
BTC Price

↓

Millions of Requests

↓

Exchange Rate Key
```

---

## Feature Flags

```
Application

↓

Global Config

↓

Millions of Reads
```

Configuration keys often become hot keys.

---

# Common Production Use Cases

Hot key mitigation is important for:

- Product pages
- Trending news
- Homepage APIs
- Dashboard widgets
- Exchange rates
- Recommendation services
- Leaderboards
- Authentication tokens
- Feature flags
- Global configuration

---

# Common Mistakes

## Assuming Redis Cluster Solves Everything

Redis Cluster distributes **keys**, not **requests**.

One hot key still belongs to one slot.

---

## Single Global Configuration Key

Instead of

```
config
```

Consider splitting

```
config:feature

config:ui

config:payment
```

Smaller keys distribute traffic more effectively.

---

## Ignoring Monitoring

Monitor:

- CPU
- Network bandwidth
- Per-key request counts
- Latency
- Slowlog

---

## No Local Cache

Repeatedly reading the same configuration from Redis wastes network bandwidth.

Frequently accessed immutable data can often be cached inside the application.

---

# Best Practices

- Continuously identify hot keys using monitoring tools.
- Cache immutable or rarely changing hot data locally within application instances.
- Use Redis replicas to distribute read traffic.
- Shard extremely hot keys when a single key becomes a bottleneck.
- Combine browser cache, CDN, application cache, and Redis for layered caching.
- Rate-limit abusive clients.
- Monitor CPU utilization, network throughput, and per-key request frequency.

---

# Performance Considerations

| Technique | Redis Load | Complexity | Scalability |
|------------|------------|------------|-------------|
| Local Cache | Very Low | Low | Excellent |
| Read Replicas | Low | Medium | Excellent |
| Key Sharding | Very Low | High | Excellent |
| CDN | Very Low | Medium | Excellent |
| Multi-Level Cache | Extremely Low | High | Excellent |
| Request Coalescing | Low | Medium | Good |
| Rate Limiting | Low | Medium | Good |

---

# Production Considerations

For production deployments:

- Monitor hot keys continuously using Redis monitoring tools and application metrics.
- Place frequently accessed immutable data in local application caches where appropriate.
- Use Redis replicas to scale read-heavy workloads.
- Shard exceptionally hot keys only when replication alone is insufficient.
- Keep hot values relatively small to minimize serialization and network overhead.
- Combine Redis with CDNs and edge caches for globally distributed applications.
- Test flash-sale and traffic-spike scenarios before production releases.

---

# Decision Guide

| Scenario | Recommended Solution |
|----------|----------------------|
| Product Flash Sale | Replicas + Local Cache |
| Homepage | CDN + Local Cache |
| Exchange Rates | Local Cache + Refresh Ahead |
| Feature Flags | Local Cache |
| Trending News | CDN + Redis Replicas |
| Dashboard Metrics | Refresh Ahead + Replicas |
| Celebrity Profile | Key Sharding + Replicas |
| Global Configuration | Local Cache |

---

# Summary

A Hot Key is a Redis key that receives a disproportionately large amount of traffic, potentially overwhelming a single Redis node even in a clustered deployment. Unlike cache stampedes or avalanches, the problem is not cache expiration but traffic concentration. Effective mitigation techniques include local application caching, Redis read replicas, key sharding, CDNs, multi-level caching, request coalescing, and rate limiting. Identifying and addressing hot keys is essential for maintaining predictable latency and achieving horizontal scalability in high-traffic systems.

---

# Key Takeaways

- A Hot Key is accessed far more frequently than other keys.
- Redis Cluster distributes keys, not request volume, so a single hot key can overload one node.
- Monitor hot keys using `redis-cli --hotkeys`, command statistics, and application metrics.
- Local application caches are one of the most effective solutions for immutable hot data.
- Read replicas distribute traffic for read-heavy workloads.
- Key sharding can eliminate bottlenecks for extremely hot keys.
- Multi-level caching (browser, CDN, application, Redis) provides the best scalability.
- Regular monitoring and traffic analysis are essential to detect hot keys before they impact production.