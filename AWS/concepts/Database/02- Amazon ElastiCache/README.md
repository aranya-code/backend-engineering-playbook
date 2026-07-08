# Amazon ElastiCache

A comprehensive deep-dive into Amazon ElastiCache — AWS's fully managed in-memory caching service supporting Redis and Memcached engines. These notes cover caching patterns, engine selection, replication, clustering, eviction policies, failure scenarios, security, monitoring, and the comparison with Amazon MemoryDB.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [Overview and Caching Patterns](./01-%20Overview%20and%20Caching%20Patterns.md) | Cache-Aside, Write-Through, Write-Back, Read-Through, hit/miss mechanics |
| 02 | [Redis vs Memcached](./02-%20Redis%20vs%20Memcached.md) | Threading models, data structures, persistence, replication, HA, selection guide |
| 03 | [Redis Replication and Clusters](./03-%20Redis%20Replication%20and%20Clusters.md) | Master-replica, Cluster Mode Enabled/Disabled, Hash Slots, Hash Tags |
| 04 | [Cache Eviction and TTL](./04-%20Cache%20Eviction%20and%20TTL.md) | LRU, LFU, volatile vs allkeys policies, active/passive TTL expiration |
| 05 | [Cache Failure Scenarios and Mitigations](./05-%20Cache%20Failure%20Scenarios%20and%20Mitigations.md) | Cache Stampede, Cache Penetration, Cache Avalanche, Cache Warmup |
| 06 | [Security and Monitoring](./06-%20Security%20and%20Monitoring.md) | VPC isolation, RBAC, AUTH, TLS, EngineCPUUtilization vs CPUUtilization |
| 07 | [Best Practices and MemoryDB](./07-%20Best%20Practices%20and%20MemoryDB.md) | ElastiCache vs MemoryDB, reserved memory, swap monitoring, key naming |

---

# Quick Reference

```text
Caching Architecture:

Application ──► Check Cache ──► Hit? ──► Return Data (Sub-ms)
                    │
                   Miss
                    │
                    ▼
              Query Database ──► Write to Cache ──► Return Data
```

## Key Numbers to Remember

| Metric | Value |
|--------|-------|
| Max Replicas per Shard | 5 |
| Max Shards (Cluster Mode) | 500 |
| Hash Slots | 16,384 |
| Redis Max Value Size | 512 MB |
| Memcached Max Value Size | 1 MB |
| Reserved Memory (recommended) | 25% |

## Critical Monitoring Rule

```text
DO NOT alert on CPUUtilization for Redis.
Redis is single-threaded for command execution.

On a 4-vCPU host at 100% engine saturation:
  CPUUtilization      = 25%  ← MISLEADING
  EngineCPUUtilization = 100% ← ACCURATE

Always monitor and alert on EngineCPUUtilization.
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Database Module](../README.md) |
| ⬅️ Previous | [Amazon RDS](../01-%20Amazon%20RDS/) |
| ➡️ Next | [Comparison Guide](../03-%20Comparison%20Guide/) |

---
