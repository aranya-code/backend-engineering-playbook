# Redis Production Cheat Sheet

## Overview

Redis is widely used in production systems for caching, session management, real-time analytics, distributed locking, messaging, and rate limiting. Running Redis in production requires more than just storing data—it involves high availability, durability, security, monitoring, backups, and performance tuning.

This cheat sheet provides a concise reference for deploying and operating Redis in production environments.

---

# Production Architecture

```text
                Clients
                   │
                   ▼
            Load Balancer
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Application A         Application B
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
            Redis Cluster
      ┌────────┬────────┬────────┐
      ▼        ▼        ▼
   Master    Master    Master
      │         │         │
      ▼         ▼         ▼
   Replica   Replica   Replica
```

---

# Production Deployment Checklist

| Category | Recommendation |
|----------|----------------|
| High Availability | Use Replication + Sentinel or Cluster |
| Security | Enable ACLs, TLS, Authentication |
| Monitoring | Collect metrics continuously |
| Persistence | Configure RDB and AOF appropriately |
| Memory | Set `maxmemory` and eviction policy |
| Scaling | Use Redis Cluster when needed |
| Backups | Automate snapshots and recovery testing |
| Clients | Use connection pooling |

---

# Memory Configuration

Check memory usage:

```bash
INFO MEMORY
```

Set a memory limit:

```bash
CONFIG SET maxmemory 8gb
```

Choose an eviction policy:

```bash
CONFIG SET maxmemory-policy allkeys-lru
```

---

# Recommended Eviction Policies

| Use Case | Policy |
|----------|--------|
| General Cache | allkeys-lru |
| Frequently Accessed Cache | allkeys-lfu |
| Expiring Data | volatile-lru |
| Strict Persistence | noeviction |

---

# Persistence Strategy

## RDB

Pros

- Fast restart
- Compact backups
- Low runtime overhead

Cons

- Possible data loss between snapshots

---

## AOF

Pros

- Better durability
- More frequent persistence

Cons

- Larger files
- Slightly higher write overhead

---

## Recommended Production Configuration

```text
RDB

+

AOF

↓

Balanced durability and recovery
```

---

# High Availability

## Replication

```text
          Master
         /      \
        ▼        ▼
   Replica1  Replica2
```

Benefits

- Read scaling
- Failover support
- Data redundancy

---

## Sentinel

```text
      Sentinel
          │
          ▼
      Master
      /     \
Replica    Replica
```

Responsibilities

- Health monitoring
- Automatic failover
- Service discovery
- Notifications

---

## Redis Cluster

```text
Master 1

↓

Replica

Master 2

↓

Replica

Master 3

↓

Replica
```

Benefits

- Horizontal scaling
- Automatic partitioning
- High availability

---

# Security Checklist

Enable authentication:

```bash
ACL LIST

ACL WHOAMI
```

Enable TLS

Disable dangerous commands where possible

Restrict network access using firewalls or security groups

Run Redis on private networks

Keep Redis updated

---

# Client Best Practices

Use

- Connection pooling
- Retry logic
- Exponential backoff
- Timeouts
- Health checks

Avoid

- Opening a new connection for every request
- Infinite retries
- Long blocking operations

---

# Monitoring Commands

| Command | Purpose |
|----------|----------|
| INFO | General health |
| INFO MEMORY | Memory usage |
| INFO CPU | CPU usage |
| INFO STATS | Statistics |
| INFO REPLICATION | Replication status |
| CLIENT LIST | Connected clients |
| SLOWLOG GET | Slow commands |
| LATENCY DOCTOR | Latency analysis |

---

# Important Metrics

| Metric | Healthy Target |
|----------|----------------|
| Latency | < 1 ms |
| Cache Hit Ratio | > 90% |
| Memory Usage | < 80% |
| Evictions | Minimal |
| Connected Clients | Within configured limits |
| Replica Lag | Near zero |
| Fragmentation Ratio | ~1.0–1.5 |

---

# Backup Strategy

Recommended schedule:

```text
Hourly

↓

Daily Snapshot

↓

Weekly Backup

↓

Monthly Archive
```

Best Practices

- Store backups offsite.
- Encrypt backup files.
- Test restoration regularly.
- Automate backup creation.

---

# Disaster Recovery Workflow

```text
Failure

↓

Identify Cause

↓

Restore Backup

↓

Verify Data

↓

Reconnect Applications

↓

Monitor System
```

---

# Scaling Strategy

### Vertical Scaling

Increase

- CPU
- RAM
- Faster storage
- Network bandwidth

Suitable for:

- Small to medium workloads

---

### Horizontal Scaling

Use Redis Cluster

Benefits

- More capacity
- Higher throughput
- Fault tolerance

---

# Performance Best Practices

- Use appropriate data structures.
- Set TTLs for cache entries.
- Keep values reasonably small.
- Prefer `SCAN` over `KEYS`.
- Use pipelining for bulk operations.
- Monitor slow queries.
- Use replicas for read-heavy workloads.
- Avoid hot keys.

---

# Common Production Problems

| Problem | Typical Solution |
|----------|------------------|
| High memory usage | Optimize data model, configure eviction |
| High CPU | Remove expensive commands, optimize access patterns |
| Slow responses | Check Slow Log and latency metrics |
| Replica lag | Improve network, reduce write pressure |
| Frequent evictions | Increase memory or adjust TTL strategy |
| Connection spikes | Enable connection pooling |

---

# Operational Commands

Check server health:

```bash
INFO
```

Check clients:

```bash
CLIENT LIST
```

Inspect slow commands:

```bash
SLOWLOG GET
```

Analyze latency:

```bash
LATENCY DOCTOR
```

Review memory:

```bash
INFO MEMORY
```

---

# Production Readiness Checklist

| Item | Status |
|------|--------|
| Authentication enabled | ✓ |
| ACL configured | ✓ |
| TLS enabled | ✓ |
| Persistence configured | ✓ |
| Replication configured | ✓ |
| Monitoring enabled | ✓ |
| Alerts configured | ✓ |
| Backups automated | ✓ |
| Recovery tested | ✓ |
| Connection pooling enabled | ✓ |

---

# Daily Operations Checklist

```text
Morning

↓

Check Alerts

↓

Review Memory

↓

Review CPU

↓

Review Slow Log

↓

Verify Replication

↓

Check Backups

↓

Review Cache Hit Ratio
```

---

# Common Mistakes

| Mistake | Better Practice |
|----------|-----------------|
| Running without authentication | Enable ACLs and passwords |
| No backups | Automate backups |
| No memory limit | Configure `maxmemory` |
| Ignoring slow queries | Monitor `SLOWLOG` regularly |
| Using a single Redis instance for critical workloads | Deploy Replication or Cluster |
| No monitoring | Integrate with monitoring and alerting systems |

---

# Production Interview Tips

Senior interviewers commonly ask:

- How would you deploy Redis for high availability?
- When would you choose Sentinel vs Cluster?
- Which persistence mode would you use and why?
- How would you secure a production Redis deployment?
- How do you investigate latency spikes?
- What metrics are most important to monitor?
- How would you recover from a Redis node failure?

A strong answer should discuss:

1. High availability architecture.
2. Persistence trade-offs.
3. Memory management.
4. Monitoring and alerting.
5. Security practices.
6. Backup and disaster recovery.
7. Scaling strategy.
8. Operational runbooks.