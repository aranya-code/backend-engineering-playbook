# Production Configuration

## Overview

A Redis instance running on a developer's laptop is very different from a Redis deployment serving millions of requests per day.

Development environments typically use:

- Single Redis instance
- No authentication
- Default configuration
- No monitoring
- No persistence tuning

Production environments require:

- High availability
- Security
- Connection pooling
- Monitoring
- Backup strategy
- Performance tuning
- Memory management
- Disaster recovery

A poorly configured Redis server can become a single point of failure for your entire application.

---

# Production Architecture

```
                    Internet

                        │

                        ▼

                 Load Balancer

                        │

          ┌─────────────┴─────────────┐

          ▼                           ▼

      Django                     FastAPI

          │                           │

          └─────────────┬─────────────┘

                        ▼

             Redis Connection Pool

                        │

                Redis Sentinel

         ┌──────────────┼──────────────┐

         ▼              ▼              ▼

    Primary         Replica 1      Replica 2

                        │

                        ▼

                  Backup Storage
```

---

# Redis Deployment Options

| Deployment | Recommended |
|------------|-------------|
| Local Redis | Development |
| Docker | Development / Testing |
| VM | Small Production |
| Kubernetes | Production |
| AWS ElastiCache | Enterprise |
| Azure Cache for Redis | Enterprise |
| Redis Cloud | Managed Production |

---

# Environment Variables

Never hardcode configuration.

Example

```
REDIS_HOST=redis

REDIS_PORT=6379

REDIS_DB=0

REDIS_PASSWORD=StrongPassword

REDIS_SSL=True
```

Django

```python
import os

REDIS_HOST = os.getenv("REDIS_HOST")
```

---

# Production Redis URL

Instead of

```
redis://localhost:6379
```

Use

```
redis://:password@redis.example.com:6379/0
```

TLS

```
rediss://:password@redis.example.com:6379/0
```

---

# Django Configuration

```python
CACHES = {

    "default": {

        "BACKEND":

        "django_redis.cache.RedisCache",

        "LOCATION":

        os.getenv("REDIS_URL"),

        "OPTIONS": {

            "CLIENT_CLASS":

            "django_redis.client.DefaultClient"

        }
    }
}
```

---

# FastAPI Configuration

```
config.py
```

```python
from redis.asyncio import Redis

redis_client = Redis(

    host=os.getenv("REDIS_HOST"),

    port=int(os.getenv("REDIS_PORT")),

    password=os.getenv("REDIS_PASSWORD"),

    decode_responses=True
)
```

---

# Docker Deployment

```
services:

    redis:

        image: redis:7

        restart: always

        ports:

            - "6379:6379"
```

Production should avoid exposing Redis publicly.

---

# Docker Compose Architecture

```
Docker Network

│

├── Django

├── FastAPI

├── Redis

├── PostgreSQL

└── Celery
```

Applications communicate internally.

---

# Redis Authentication

Enable password authentication.

```
redis.conf

↓

requirepass

↓

StrongPassword
```

Python

```python
Redis(

    password="StrongPassword"
)
```

---

# TLS Encryption

Production

```
Application

↓

TLS

↓

Redis
```

Protects data in transit.

Connection

```
rediss://
```

instead of

```
redis://
```

---

# Connection Pooling

Always use pooling.

```
Application

↓

Connection Pool

↓

Redis
```

Never create a new connection for every request.

---

# Connection Pool Example

```python
pool = redis.ConnectionPool(

    max_connections=100,

    socket_timeout=5,

    socket_connect_timeout=5
)
```

---

# Separate Redis Databases

Example

```
DB 0

Cache
```

```
DB 1

Sessions
```

```
DB 2

Celery Broker
```

```
DB 3

Rate Limiting
```

Better isolation.

> **Production Note:** In large systems, using separate Redis instances or key namespaces is often preferred over logical databases because Redis Cluster supports only database `0`.

---

# Key Prefixes

Instead of

```
products
```

Use

```
cache:products
```

```
session:abc123
```

```
rate:user:15
```

```
celery:task:102
```

Namespaces simplify maintenance.

---

# High Availability

Single Redis

```
Application

↓

Redis

↓

Failure

↓

Application Down
```

---

Redis Sentinel

```
Application

↓

Sentinel

↓

Primary

↓

Replica
```

Automatic failover.

---

# Redis Cluster

Large deployments

```
          Cluster

   ┌────────┼────────┐

   ▼        ▼        ▼

 Node1   Node2   Node3

   │        │        │

 Slots   Slots   Slots
```

Supports horizontal scaling.

---

# Persistence

Redis supports

- RDB
- AOF

Configuration

```
Redis

↓

Memory

↓

Disk
```

Persistence protects against data loss.

---

# RDB Snapshots

```
Memory

↓

Snapshot

↓

dump.rdb
```

Fast recovery.

Suitable for

- Caching
- Analytics
- Read-heavy systems

---

# AOF

```
SET

↓

Append

↓

appendonly.aof
```

Better durability.

Tradeoff

Slightly slower writes.

---

# Hybrid Persistence

Production recommendation

```
AOF

+

RDB
```

Best balance between durability and recovery speed.

---

# Memory Configuration

Configure

```
maxmemory
```

Example

```
maxmemory 8gb
```

Without limits

```
Redis

↓

Memory Full

↓

Crash Risk
```

---

# Eviction Policy

Recommended

```
allkeys-lru
```

Other options

- volatile-lru
- volatile-ttl
- allkeys-lfu
- noeviction

Choose based on workload.

---

# Monitoring

Monitor

- Memory usage
- Hit ratio
- Miss ratio
- Latency
- Slow commands
- Evictions
- Connected clients

Useful commands

```
INFO

INFO MEMORY

INFO STATS

CLIENT LIST

SLOWLOG GET
```

---

# Logging

Enable

```
Slow Log

Latency Monitor

Redis Logs
```

Detect

- Slow commands
- Blocking operations
- Large keys

---

# Backup Strategy

Example

```
Redis

↓

Nightly Snapshot

↓

Cloud Storage
```

Retention

```
Daily

Weekly

Monthly
```

---

# Disaster Recovery

```
Primary Failure

↓

Replica Promotion

↓

Application Continues
```

Backups

↓

Restore

↓

Resume Operations

---

# Security Checklist

Enable

- Authentication
- TLS
- Firewall
- Private Network
- ACLs
- Monitoring

Disable

- Public Redis
- Anonymous access
- Dangerous commands (if appropriate)

---

# Redis ACL

Redis 6+

```
User

↓

Permissions

↓

Allowed Commands
```

Example

```
Developer

↓

Read Only
```

Operations team

```
Read

Write

Admin
```

---

# Timeouts

Configure

```
socket_timeout

socket_connect_timeout
```

Prevent

```
Broken Network

↓

Application Hang
```

---

# Resource Limits

Monitor

- CPU
- RAM
- Network bandwidth
- Disk I/O
- Connection count

Scale before bottlenecks occur.

---

# Production Monitoring Stack

```
Redis

↓

Prometheus

↓

Grafana

↓

Alerts
```

Alerts

- High memory
- High latency
- Replication lag
- Failover
- Low hit ratio

---

# Kubernetes Deployment

```
Pods

│

├── Django

├── FastAPI

├── Redis

├── Celery

└── PostgreSQL
```

Redis often uses

- StatefulSets
- Persistent Volumes
- Readiness probes
- Liveness probes

---

# AWS Architecture

```
Application

↓

ElastiCache Redis

↓

Multi-AZ

↓

Automatic Failover
```

Benefits

- Managed service
- Backups
- Monitoring
- Scaling
- Security

---

# Azure Architecture

```
App Service

↓

Azure Redis Cache

↓

Monitoring

↓

Failover
```

---

# Common Production Use Cases

Production Redis configuration is essential for:

- E-commerce platforms
- Banking applications
- Healthcare systems
- AI platforms
- SaaS products
- Gaming platforms
- IoT backends
- Real-time analytics
- High-volume APIs
- Microservices

---

# Common Mistakes

## Running Without Authentication

Bad

```
Redis

↓

Public Internet
```

Anyone can access data.

---

## Unlimited Memory

Without

```
maxmemory
```

Redis can exhaust system RAM.

---

## No Monitoring

Problems remain unnoticed until applications fail.

---

## Using Default Configuration

Default settings are intended for development, not production.

---

## No Backup

Server failure

↓

Everything lost.

---

## No Replication

Single Redis instance

↓

Single point of failure.

---

## Sharing One Database for Everything

```
Cache

Sessions

Celery

Rate Limits

↓

DB0
```

Harder to manage and monitor.

---

# Best Practices

- Secure Redis with passwords, ACLs, TLS, and private networking.
- Use environment variables for all configuration.
- Configure connection pooling in all applications.
- Enable RDB and AOF persistence where durability is required.
- Set `maxmemory` and an appropriate eviction policy.
- Deploy Redis Sentinel or Cluster for high availability.
- Implement automated backups and disaster recovery procedures.
- Continuously monitor Redis health, latency, replication, and memory usage.

---

# Performance Considerations

| Configuration | Benefit |
|---------------|----------|
| Connection Pooling | Lower latency |
| Redis Cluster | Horizontal scaling |
| Sentinel | High availability |
| RDB + AOF | Fast recovery + durability |
| Maxmemory | Prevents OOM |
| Eviction Policy | Stable cache performance |
| Monitoring | Early issue detection |

---

# Production Checklist

| Item | Status |
|-------|--------|
| Authentication Enabled | ✅ |
| TLS Enabled | ✅ |
| Connection Pooling | ✅ |
| Environment Variables | ✅ |
| Monitoring Configured | ✅ |
| Backups Scheduled | ✅ |
| Sentinel or Cluster | ✅ |
| Memory Limits Configured | ✅ |
| Eviction Policy Selected | ✅ |
| Disaster Recovery Tested | ✅ |

---

# Summary

A production-ready Redis deployment requires much more than simply installing Redis. Proper security, connection pooling, high availability, persistence, monitoring, memory management, and disaster recovery are essential for building reliable backend systems. Whether deploying on virtual machines, Kubernetes, or managed cloud services such as Amazon ElastiCache or Azure Cache for Redis, a well-configured Redis infrastructure ensures scalability, resilience, and operational stability.

---

# Key Takeaways

- Never use development Redis settings in production.
- Secure Redis with authentication, TLS, ACLs, and private networking.
- Use connection pooling in all Django and FastAPI applications.
- Configure `maxmemory` and an appropriate eviction policy.
- Enable RDB and AOF persistence when durability matters.
- Deploy Sentinel or Redis Cluster for high availability.
- Continuously monitor latency, memory, replication, and cache hit ratio.
- Maintain automated backups and regularly test disaster recovery procedures.