# Redis

A comprehensive, senior-level knowledge base covering Redis from core data structures and caching patterns to production deployment, scaling, troubleshooting, Python framework integration, and interview preparation.

These notes are written for **Senior Backend Engineers**, **DevOps Engineers**, and **Solutions Architects** who need to design, implement, and operate Redis-backed systems in production.

---

## Why Redis?

Redis is an in-memory data structure store used as a database, cache, message broker, and streaming engine. It delivers **sub-millisecond latency** with support for rich data structures that go far beyond simple key-value storage.

```text
┌──────────────────────────────────────────────────────────────────┐
│                       Redis Architecture                         │
│                                                                  │
│   Application                                                    │
│       │                                                          │
│       ▼                                                          │
│   ┌──────────────┐    ┌────────────────────────────────────┐    │
│   │  Redis Client│───▶│         Redis Server               │    │
│   │  (redis-py,  │    │                                    │    │
│   │   django-    │    │  ┌─────────────────────────────┐   │    │
│   │   redis,     │    │  │    In-Memory Data Store     │   │    │
│   │   aioredis)  │    │  │                             │   │    │
│   └──────────────┘    │  │  Strings · Lists · Sets     │   │    │
│                       │  │  Sorted Sets · Hashes       │   │    │
│                       │  │  Streams · HyperLogLog      │   │    │
│                       │  │  Bitmaps · Geospatial       │   │    │
│                       │  └─────────────────────────────┘   │    │
│                       │                                    │    │
│                       │  ┌──────────┐    ┌─────────────┐   │    │
│                       │  │ RDB/AOF  │    │  Pub/Sub    │   │    │
│                       │  │ Persist  │    │  Streams    │   │    │
│                       │  └──────────┘    └─────────────┘   │    │
│                       └────────────────────────────────────┘    │
│                                                                  │
│   HA Options:  Sentinel (failover)  ·  Cluster (sharding)       │
│   Cloud:       AWS ElastiCache  ·  AWS MemoryDB                 │
└──────────────────────────────────────────────────────────────────┘
```

**When to use Redis:**
- Caching (response cache, session store, query cache)
- Rate limiting, leaderboards, counters
- Real-time messaging (Pub/Sub, Streams)
- Distributed locking
- Session management for web applications
- Job queues (Celery broker, Sidekiq)
- Geospatial indexing

**When Redis is NOT the right choice:**
- Primary database for relational data → use PostgreSQL / MySQL
- Full-text search → use Elasticsearch / OpenSearch
- Data larger than available RAM → use disk-based databases
- Complex queries with JOINs → use a relational database

---

## Module Index

This knowledge base contains **113 content files** across **9 modules**, organized as a progressive learning path.

| # | Module | Files | Focus |
|---|--------|-------|-------|
| 01 | [Concepts](./01-%20Concepts/) | 24 | Fundamentals, data structures, persistence, replication, transactions, Pub/Sub, locking, Sentinel, Cluster, sharding, memory, security |
| 02 | [CLI](./02-%20CLI/) | 14 | Redis CLI basics, commands for every data type, transactions, Pub/Sub, TTL, server management, configuration |
| 03 | [Caching](./03-%20Caching/) | 14 | Caching patterns (cache-aside, read-through, write-through, write-behind, refresh-ahead), eviction, stampede, avalanche, penetration, hot keys, rate limiting |
| 04 | [Django & FastAPI Integration](./04-%20Django%20and%20FastAPI%20Integration/) | 11 | django-redis, cache framework, sessions, FastAPI async Redis, connection pooling, Celery, background tasks, response caching, production config |
| 05 | [Production](./05-%20Production/) | 9 | Deployment, scaling, high availability, monitoring, performance tuning, backup/restore, benchmarking, Kubernetes, AWS ElastiCache |
| 06 | [Troubleshooting](./06-%20Troubleshooting/) | 14 | Startup failures, connection issues, auth, memory/eviction, latency, replication, Sentinel, Cluster, persistence, slow commands, Docker/K8s, ElastiCache, incident playbook |
| 07 | [Cheatsheets](./07-%20Cheatsheets/) | 7 | Quick reference cards for CLI, data structures, performance, production, interviews, system design, command reference |
| 08 | [Interview](./08-%20Interview/) | 12 | Fundamentals, data structures, caching, persistence, HA, Cluster, performance, production scenarios, system design, senior-level, coding, company-specific |
| 09 | [Sample Projects](./09-%20Sample%20Projects/) | 2 projects | `django-redis-lab` and `fastapi-redis-lab` — complete runnable projects demonstrating 12 Redis features each |

---

## Learning Path

```text
┌──────────────────────────┐
│  01- Concepts            │  Start here
│  Fundamentals, data      │
│  structures, persistence,│
│  replication, Cluster    │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  02- CLI                 │  Learn the tool
│  Commands for every      │
│  data type + server ops  │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  03- Caching             │  Core use case
│  Patterns, eviction,     │
│  stampede, consistency   │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  04- Django & FastAPI     │  Apply in code
│  Integration             │
│  django-redis, async,    │
│  Celery, sessions        │
└────────────┬─────────────┘
             │
     ┌───────┴───────┐
     │               │
┌────▼────┐   ┌──────▼──────┐
│ 05-     │   │ 06-         │  Run & fix
│ Prod    │   │ Trouble-    │
│         │   │ shooting    │
└────┬────┘   └──────┬──────┘
     │               │
     └───────┬───────┘
             │
┌────────────▼─────────────┐
│  07- Cheatsheets         │  Quick reference
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  08- Interview           │  Validate knowledge
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  09- Sample Projects     │  Hands-on code
│  django-redis-lab        │
│  fastapi-redis-lab       │
└──────────────────────────┘
```

---

## Module Breakdown

### 01 — Concepts (24 files)

Core Redis knowledge across three sub-modules.

#### 01- Fundamentals (12 files)

| # | File | Topic |
|---|------|-------|
| 01 | [Introduction](./01-%20Concepts/01-%20Fundamentals/01-%20Introduction.md) | What Redis is, architecture, use cases |
| 02 | [Redis Architecture](./01-%20Concepts/01-%20Fundamentals/02-%20Redis%20Architecture.md) | Single-threaded model, event loop, I/O multiplexing |
| 03 | [Installing Redis](./01-%20Concepts/01-%20Fundamentals/03-%20Installing%20Redis.md) | Installation on Linux, macOS, Windows, Docker |
| 04 | [Strings](./01-%20Concepts/01-%20Fundamentals/04-%20Strings.md) | SET, GET, INCR, MSET, bit operations |
| 05 | [Lists](./01-%20Concepts/01-%20Fundamentals/05-%20Lists.md) | LPUSH, RPUSH, LPOP, LRANGE, blocking pops |
| 06 | [Sets](./01-%20Concepts/01-%20Fundamentals/06-%20Sets.md) | SADD, SMEMBERS, SINTER, SUNION, SDIFF |
| 07 | [Sorted Sets](./01-%20Concepts/01-%20Fundamentals/07-%20Sorted%20Sets.md) | ZADD, ZRANGE, ZRANK, leaderboards |
| 08 | [Hashes](./01-%20Concepts/01-%20Fundamentals/08-%20Hashes.md) | HSET, HGET, HGETALL, object storage |
| 09 | [Streams](./01-%20Concepts/01-%20Fundamentals/09-%20Streams.md) | XADD, XREAD, consumer groups, event logs |
| 10 | [Redis JSON](./01-%20Concepts/01-%20Fundamentals/10-%20Redis%20JSON.md) | JSON.SET, JSON.GET, nested queries |
| 11 | [Redis Search](./01-%20Concepts/01-%20Fundamentals/11-%20Redis%20Search.md) | Full-text search, indexing, aggregations |
| 12 | [Redis TimeSeries](./01-%20Concepts/01-%20Fundamentals/12-%20Redis%20TimeSeries.md) | Time-series data, downsampling, retention |

#### 02- Data Persistence (7 files)

| # | File | Topic |
|---|------|-------|
| 13 | [Expiration & TTL](./01-%20Concepts/02-%20Data%20persistence/13-%20Expiration%20%26%20TTL.md) | EXPIRE, TTL, key lifecycle |
| 14 | [Persistence (RDB vs AOF)](./01-%20Concepts/02-%20Data%20persistence/14-%20Persistence%20(RDB%20vs%20AOF).md) | Snapshots vs append-only files |
| 15 | [Replication](./01-%20Concepts/02-%20Data%20persistence/15-%20Replication.md) | Master-replica, async replication |
| 16 | [Transactions](./01-%20Concepts/02-%20Data%20persistence/16-%20Transactions.md) | MULTI, EXEC, WATCH, optimistic locking |
| 17 | [Pipelines](./01-%20Concepts/02-%20Data%20persistence/17-%20Pipelines.md) | Batch commands, reduce round trips |
| 18 | [Pub/Sub](./01-%20Concepts/02-%20Data%20persistence/18-%20Pub-Sub.md) | PUBLISH, SUBSCRIBE, pattern subscriptions |
| 19 | [Distributed Locking](./01-%20Concepts/02-%20Data%20persistence/19-%20Distributed%20Locking.md) | SET NX EX, Redlock algorithm |

#### 03- Scaling (5 files)

| # | File | Topic |
|---|------|-------|
| 20 | [Redis Sentinel](./01-%20Concepts/03-%20Scaling/20-%20Redis%20Sentinel.md) | Automatic failover, monitoring |
| 21 | [Redis Cluster](./01-%20Concepts/03-%20Scaling/21-%20Redis%20Cluster.md) | Hash slots, multi-node sharding |
| 22 | [Sharding](./01-%20Concepts/03-%20Scaling/22-%20Sharding.md) | Client-side, proxy, cluster sharding |
| 23 | [Memory Management & Eviction](./01-%20Concepts/03-%20Scaling/23-%20Memory%20Management%20%26%20Eviction.md) | maxmemory, eviction policies, memory optimization |
| 24 | [Redis Security](./01-%20Concepts/03-%20Scaling/24-%20Redis%20Security.md) | AUTH, ACL, TLS, network hardening |

---

### 02 — CLI (14 files)

Hands-on command reference for every Redis data type and server operation.

| # | File | Topic |
|---|------|-------|
| 01 | [Redis CLI Basics](./02-%20CLI/01-%20Redis%20CLI%20Basics.md) | Connecting, redis-cli modes, output formatting |
| 02 | [Keys Commands](./02-%20CLI/02-%20Keys%20Commands.md) | KEYS, SCAN, EXISTS, TYPE, RENAME, DEL |
| 03 | [String Commands](./02-%20CLI/03-%20String%20Commands.md) | SET, GET, INCR, APPEND, SETEX |
| 04 | [List Commands](./02-%20CLI/04-%20List%20Commands.md) | LPUSH, RPUSH, LPOP, LRANGE, BLPOP |
| 05 | [Set Commands](./02-%20CLI/05-%20Set%20Commands.md) | SADD, SMEMBERS, SINTER, SUNION |
| 06 | [Sorted Set Commands](./02-%20CLI/06-%20Sorted%20Set%20Commands.md) | ZADD, ZRANGE, ZRANK, ZINCRBY |
| 07 | [Hash Commands](./02-%20CLI/07-%20Hash%20Commands.md) | HSET, HGET, HGETALL, HDEL |
| 08 | [Stream Commands](./02-%20CLI/08-%20Stream%20Commands.md) | XADD, XREAD, XRANGE, consumer groups |
| 09 | [Transaction Commands](./02-%20CLI/09-%20Transaction%20Commands.md) | MULTI, EXEC, DISCARD, WATCH |
| 10 | [Pub/Sub Commands](./02-%20CLI/10-%20Pub-Sub%20Commands.md) | PUBLISH, SUBSCRIBE, PSUBSCRIBE |
| 11 | [Expiration & TTL Commands](./02-%20CLI/11-%20Expiration%20%26%20TTL%20Commands.md) | EXPIRE, TTL, PTTL, PERSIST |
| 12 | [Server Commands](./02-%20CLI/12-%20Server%20Commands.md) | INFO, DBSIZE, FLUSHDB, SLOWLOG, DEBUG |
| 13 | [Configuration Commands](./02-%20CLI/13-%20Configuration%20Commands.md) | CONFIG GET/SET, runtime tuning |
| 14 | [Redis CLI Cheat Sheet](./02-%20CLI/14-%20Redis%20CLI%20Cheat%20Sheet.md) | Quick reference card |

---

### 03 — Caching (14 files)

Deep dive into caching patterns, failure modes, and real-world strategies.

| # | File | Topic |
|---|------|-------|
| 01 | [Caching Fundamentals](./03-%20Caching/01-%20Caching%20Fundamentals.md) | Why cache, cache layers, TTL strategies |
| 02 | [Cache-Aside Pattern](./03-%20Caching/02-%20Cache%20Aside%20Pattern.md) | Lazy loading — app manages cache |
| 03 | [Read-Through Cache](./03-%20Caching/03-%20Read%20Through%20Cache.md) | Cache provider loads on miss |
| 04 | [Write-Through Cache](./03-%20Caching/04-%20Write%20Through%20Cache.md) | Sync write to cache + DB |
| 05 | [Write-Behind Cache](./03-%20Caching/05-%20Write%20Behind%20Cache.md) | Async write-back to DB |
| 06 | [Refresh-Ahead Cache](./03-%20Caching/06-%20Refresh%20Ahead%20Cache.md) | Proactive refresh before expiry |
| 07 | [Cache Eviction Strategies](./03-%20Caching/07-%20Cache%20Eviction%20Strategies.md) | LRU, LFU, TTL-based, allkeys vs volatile |
| 08 | [Cache Stampede](./03-%20Caching/08-%20Cache%20Stampede.md) | Thundering herd prevention |
| 09 | [Cache Avalanche](./03-%20Caching/09-%20Cache%20Avalanche.md) | Mass expiration cascading to DB |
| 10 | [Cache Penetration](./03-%20Caching/10-%20Cache%20Penetration.md) | Querying non-existent keys |
| 11 | [Cache Consistency](./03-%20Caching/11-%20Cache%20Consistency.md) | Invalidation, eventual consistency, dual-write |
| 12 | [Hot Keys](./03-%20Caching/12-%20Hot%20Keys.md) | Detecting and mitigating hot spots |
| 13 | [Rate Limiting](./03-%20Caching/13-%20Rate%20Limiting.md) | Token bucket, sliding window, INCR+EXPIRE |
| 14 | [Real-World Caching Examples](./03-%20Caching/14-%20Real%20World%20Caching%20Examples.md) | Production caching architectures |

---

### 04 — Django & FastAPI Integration (11 files)

How to integrate Redis with Python web frameworks for caching, sessions, background tasks, and async patterns.

| # | File | Topic |
|---|------|-------|
| 01 | [Redis with Django](./04-%20Django%20and%20FastAPI%20Integration/01-%20Redis%20with%20Django.md) | django-redis setup, cache backend config |
| 02 | [Django Cache Framework](./04-%20Django%20and%20FastAPI%20Integration/02-%20Django%20Cache%20Framework.md) | View cache, template cache, low-level API |
| 03 | [Django Session Storage](./04-%20Django%20and%20FastAPI%20Integration/03-%20Django%20Session%20Storage.md) | Redis-backed sessions |
| 04 | [Redis with FastAPI](./04-%20Django%20and%20FastAPI%20Integration/04-%20Redis%20with%20FastAPI.md) | redis.asyncio + FastAPI dependency injection |
| 05 | [Async Redis](./04-%20Django%20and%20FastAPI%20Integration/05-%20Async%20Redis.md) | redis.asyncio patterns, connection management |
| 06 | [Connection Pooling](./04-%20Django%20and%20FastAPI%20Integration/06-%20Connection%20Pooling.md) | Pool sizing, BlockingConnectionPool, async pools |
| 07 | [Celery with Redis](./04-%20Django%20and%20FastAPI%20Integration/07-%20Celery%20with%20Redis.md) | Redis as Celery broker and result backend |
| 08 | [Background Tasks](./04-%20Django%20and%20FastAPI%20Integration/08-%20Background%20Tasks.md) | Task patterns, retries, error handling |
| 09 | [Response Caching](./04-%20Django%20and%20FastAPI%20Integration/09-%20Response%20Caching.md) | API response caching strategies |
| 10 | [Production Configuration](./04-%20Django%20and%20FastAPI%20Integration/10-%20Production%20Configuration.md) | Timeouts, retries, health checks, failover |
| 11 | [Common Integration Mistakes](./04-%20Django%20and%20FastAPI%20Integration/11-%20Common%20Integration%20Mistakes.md) | Anti-patterns and how to fix them |

---

### 05 — Production (9 files)

Running Redis in production — deployment, scaling, monitoring, and cloud services.

| # | File | Topic |
|---|------|-------|
| 01 | [Production Deployment](./05-%20Production/01-%20Production%20Deployment.md) | Server configuration, systemd, tuning |
| 02 | [Scaling Redis](./05-%20Production/02-%20Scaling%20Redis.md) | Vertical, horizontal, read replicas, Cluster |
| 03 | [High Availability](./05-%20Production/03-%20High%20Availability.md) | Sentinel, Cluster, failover patterns |
| 04 | [Monitoring Redis](./05-%20Production/04-%20Monitoring%20Redis.md) | INFO, SLOWLOG, CloudWatch, Prometheus |
| 05 | [Performance Tuning](./05-%20Production/05-%20Performance%20Tuning.md) | Memory, network, persistence, command optimization |
| 06 | [Backup & Restore](./05-%20Production/06-%20Backup%20%26%20Restore.md) | RDB snapshots, AOF, automated backups |
| 07 | [Benchmarking](./05-%20Production/07-%20Benchmarking.md) | redis-benchmark, memtier, load testing |
| 08 | [Redis in Kubernetes](./05-%20Production/08-%20Redis%20in%20Kubernetes.md) | StatefulSet, Helm charts, Sentinel on K8s |
| 09 | [Redis in AWS](./05-%20Production/09-%20Redis%20in%20AWS.md) | ElastiCache, MemoryDB, configuration, migration |

---

### 06 — Troubleshooting (14 files)

Diagnosing and resolving every common Redis issue in production.

| # | File | Topic |
|---|------|-------|
| 01 | [Redis Won't Start](./06-%20Troubleshooting/01-%20Redis%20Won't%20Start.md) | Config errors, port conflicts, permission issues |
| 02 | [Connection Refused](./06-%20Troubleshooting/02-%20Connection%20Refused.md) | Bind address, firewall, maxclients |
| 03 | [Authentication Failures](./06-%20Troubleshooting/03-%20Authentication%20Failures.md) | AUTH, ACL, password mismatch |
| 04 | [Memory Full & Evictions](./06-%20Troubleshooting/04-%20Memory%20Full%20%26%20Evictions.md) | OOM, maxmemory, eviction policy tuning |
| 05 | [High Latency](./06-%20Troubleshooting/05-%20High%20Latency.md) | SLOWLOG, blocking commands, network issues |
| 06 | [Replication Problems](./06-%20Troubleshooting/06-%20Replication%20Problems.md) | Sync failures, replication lag, split brain |
| 07 | [Sentinel & Failover Issues](./06-%20Troubleshooting/07-%20Sentinel%20%26%20Failover%20Issues.md) | Quorum, failed failover, stale state |
| 08 | [Cluster Problems](./06-%20Troubleshooting/08-%20Cluster%20Problems.md) | Slot migration, node failures, resharding |
| 09 | [Persistence Failures](./06-%20Troubleshooting/09-%20Persistence%20Failures.md) | RDB fork failures, AOF corruption |
| 10 | [Slow Commands](./06-%20Troubleshooting/10-%20Slow%20Commands.md) | KEYS, SMEMBERS on large sets, big keys |
| 11 | [Performance Troubleshooting](./06-%20Troubleshooting/11-%20Performance%20Troubleshooting.md) | Systematic performance diagnosis |
| 12 | [Docker & Kubernetes Issues](./06-%20Troubleshooting/12-%20Docker%20%26%20Kubernetes%20Issues.md) | Container-specific Redis problems |
| 13 | [AWS ElastiCache Troubleshooting](./06-%20Troubleshooting/13-%20AWS%20ElastiCache%20Troubleshooting.md) | ElastiCache-specific diagnostics |
| 14 | [Production Incident Playbook](./06-%20Troubleshooting/14-%20Production%20Incident%20Playbook.md) | Step-by-step runbook for Redis incidents |

---

### 07 — Cheatsheets (7 files)

Quick-reference cards for daily use and exam prep.

| # | File | Topic |
|---|------|-------|
| 01 | [Redis CLI Cheat Sheet](./07-%20Cheatsheets/01-%20Redis%20CLI%20Cheat%20Sheet.md) | Essential CLI commands |
| 02 | [Data Structures Cheat Sheet](./07-%20Cheatsheets/02-%20Redis%20Data%20Structures%20Cheat%20Sheet.md) | All data types at a glance |
| 03 | [Performance Cheat Sheet](./07-%20Cheatsheets/03-%20Redis%20Performance%20Cheat%20Sheet.md) | Optimization quick reference |
| 04 | [Production Cheat Sheet](./07-%20Cheatsheets/04-%20Redis%20Production%20Cheat%20Sheet.md) | Production ops quick reference |
| 05 | [Interview Cheat Sheet](./07-%20Cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md) | Key answers for interviews |
| 06 | [System Design Cheat Sheet](./07-%20Cheatsheets/06-%20Redis%20System%20Design%20Cheat%20Sheet.md) | Redis in system design scenarios |
| 07 | [Command Reference](./07-%20Cheatsheets/07-%20Redis%20Command%20Reference.md) | Comprehensive command lookup |

---

### 08 — Interview (12 files)

Comprehensive interview preparation from fundamentals to senior-level scenarios.

| # | File | Topic |
|---|------|-------|
| 01 | [Redis Fundamentals](./08-%20Interview/01-%20Redis%20Fundamentals.md) | Core concepts and architecture |
| 02 | [Data Structures](./08-%20Interview/02-%20Data%20Structures.md) | Data type selection and trade-offs |
| 03 | [Caching](./08-%20Interview/03-%20Caching.md) | Cache patterns and failure scenarios |
| 04 | [Persistence](./08-%20Interview/04-%20Persistence.md) | RDB vs AOF, durability trade-offs |
| 05 | [Replication & High Availability](./08-%20Interview/05-%20Replication%20%26%20High%20Availability.md) | Sentinel, failover, split brain |
| 06 | [Redis Cluster](./08-%20Interview/06-%20Redis%20Cluster.md) | Sharding, hash slots, resharding |
| 07 | [Performance & Optimization](./08-%20Interview/07-%20Performance%20%26%20Optimization.md) | Latency, throughput, memory |
| 08 | [Production Scenarios](./08-%20Interview/08-%20Production%20Scenario.md) | Real-world debugging questions |
| 09 | [System Design with Redis](./08-%20Interview/09-%20System%20Design%20with%20Redis.md) | Architecture design questions |
| 10 | [Senior Backend Questions](./08-%20Interview/10-%20Senior%20Backend%20Interview%20Questions.md) | Senior-level technical depth |
| 11 | [Coding & Practical](./08-%20Interview/11-%20Redis%20Coding%20%26%20Practical%20Questions.md) | Hands-on implementation questions |
| 12 | [Company-Wise Questions](./08-%20Interview/12-%20Company%20Wise%20Interview%20Questions.md) | Company-specific Redis questions |

---

### 09 — Sample Projects (2 projects)

Complete, runnable Django and FastAPI projects demonstrating 12 Redis features each.

| Project | Framework | Features |
|---------|-----------|----------|
| [django-redis-lab](./09-%20Sample%20Projects/django-redis-lab/) | Django 5 + DRF + Celery | Cache, Cart (Hash), OTP (TTL), Rate Limiter, View Counter, Leaderboard (Sorted Set), Pub/Sub, Streams, Distributed Lock, HyperLogLog, Bitmap |
| [fastapi-redis-lab](./09-%20Sample%20Projects/fastapi-redis-lab/) | FastAPI + SQLAlchemy + Celery | Same 12 features using async `redis.asyncio` with FastAPI dependency injection |

---

## Quick Reference

### Redis Data Structures

| Structure | Commands | Use Case |
|-----------|----------|----------|
| **String** | SET, GET, INCR, MSET | Counters, caching, sessions, flags |
| **List** | LPUSH, RPUSH, LPOP, LRANGE | Queues, recent items, activity feeds |
| **Set** | SADD, SMEMBERS, SINTER | Tags, unique visitors, mutual friends |
| **Sorted Set** | ZADD, ZRANGE, ZRANK | Leaderboards, priority queues, time-based indexes |
| **Hash** | HSET, HGET, HGETALL | Objects, user profiles, shopping carts |
| **Stream** | XADD, XREAD, XREADGROUP | Event logs, message queues, audit trails |
| **HyperLogLog** | PFADD, PFCOUNT | Unique count approximation (~12 KB for any cardinality) |
| **Bitmap** | SETBIT, GETBIT, BITCOUNT | Daily active users, feature flags, bloom filters |

### Key Limits

| Resource | Limit |
|----------|-------|
| Max key size | 512 MB |
| Max value size | 512 MB |
| Max keys per database | 2³² (~4 billion) |
| Max clients | 10,000 (configurable) |
| Max databases | 16 (default, configurable) |
| Cluster max nodes | 1,000 |
| Cluster hash slots | 16,384 |

### Performance Benchmarks

```text
Typical single-node throughput:  100,000+ operations/sec
Typical latency:                 < 1 ms (p99)
Persistence overhead (RDB):      ~10-30% during BGSAVE fork
Pipeline improvement:            5-10x throughput vs individual commands
```

---

## Prerequisites

- Linux command line basics
- Basic networking (TCP, ports, DNS)
- Python experience (for integration and sample projects)
- Docker basics (for local Redis setup)
- Database fundamentals (for context on caching patterns)

---

## Who These Notes Are For

- **Senior Backend Engineers** building Redis-backed systems
- **DevOps Engineers** deploying and operating Redis in production
- **Python Developers** integrating Redis with Django / FastAPI
- **Solutions Architects** designing caching and messaging architectures
- **Interview candidates** preparing for backend and system design interviews

---
