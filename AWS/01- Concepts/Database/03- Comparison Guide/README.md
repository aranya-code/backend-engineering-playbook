# Database Comparison Guides

# Introduction

This section provides detailed, side-by-side comparisons of critical database concepts, AWS services, and backend engineering patterns. Each guide is designed for rapid reference during interviews, architecture reviews, and production incident triage.

Every comparison explains not just the differences, but when and why to choose each option based on real-world workload requirements.

---

# Contents

| # | Comparison | Key Decision |
|---|-----------|--------------|
| 01 | [RDS vs Database on EC2](./01-%20RDS%20vs%20Database%20on%20EC2.md) | Managed service vs full OS control |
| 02 | [Redis vs Memcached](./02-%20Redis%20vs%20Memcached.md) | Feature-rich cache vs raw throughput |
| 03 | [ElastiCache vs MemoryDB](./03-%20ElastiCache%20vs%20MemoryDB.md) | Volatile cache vs durable in-memory database |
| 04 | [SQL vs NoSQL](./04-%20SQL%20vs%20NoSQL.md) | Relational integrity vs horizontal scale |
| 05 | [ACID vs BASE](./05-%20ACID%20vs%20BASE.md) | Strong consistency vs high availability |
| 06 | [Multi-AZ vs Read Replica](./06-%20Multi-AZ%20vs%20Read%20Replica.md) | High availability vs read scaling |
| 07 | [Cache-Aside vs Write-Through](./07-%20Cache%20Aside%20vs%20Write%20Through.md) | Lazy loading vs proactive caching |
| 08 | [Vertical vs Horizontal Scaling](./08-%20Vertical%20vs%20Horizontal%20Scaling.md) | Scale-up vs scale-out |
| 09 | [Partitioning vs Sharding](./09-%20Partitioning%20vs%20Sharding.md) | Single-instance split vs multi-instance split |

---

# Quick Decision Matrix

| Question | Read This Guide |
|----------|----------------|
| Should I use a managed DB or run my own on EC2? | RDS vs Database on EC2 |
| Which cache engine should I pick? | Redis vs Memcached |
| Do I need a durable Redis or a volatile cache? | ElastiCache vs MemoryDB |
| Should my data model be relational or flexible? | SQL vs NoSQL |
| What consistency model does my workload need? | ACID vs BASE |
| Do I need failover protection or read scaling? | Multi-AZ vs Read Replica |
| How should I load data into my cache? | Cache-Aside vs Write-Through |
| How should I grow my database capacity? | Vertical vs Horizontal Scaling |
| How should I split large datasets? | Partitioning vs Sharding |

---

# Learning Roadmap

Read the guides in this recommended order:

```text
SQL vs NoSQL ──► ACID vs BASE ──► RDS vs Database on EC2
                                          │
                                          ▼
Multi-AZ vs Read Replica ──► Vertical vs Horizontal Scaling
                                          │
                                          ▼
Partitioning vs Sharding ──► Redis vs Memcached
                                          │
                                          ▼
ElastiCache vs MemoryDB ──► Cache-Aside vs Write-Through
```

---

# Interview Focus Areas

## AWS Database Interviews
- RDS vs EC2 (managed operations trade-offs)
- Multi-AZ vs Read Replica (HA vs scaling, sync vs async replication)
- ElastiCache vs MemoryDB (volatile cache vs durable database)

## Backend Engineering Interviews
- SQL vs NoSQL (data modeling philosophy: model-first vs query-first)
- ACID vs BASE (consistency vs availability trade-offs)
- Cache-Aside vs Write-Through (cache invalidation strategies)
- Partitioning vs Sharding (when each applies)

## System Design Interviews
- Vertical vs Horizontal Scaling (scaling limits and complexity)
- Read scaling with replicas and caches
- Database partitioning for high-write workloads

---

# Related Sections

- [Database Fundamentals](../00-%20Fundamentals/)
- [Amazon RDS](../01-%20Amazon%20RDS/)
- [Amazon ElastiCache](../02-%20Amazon%20ElastiCache/)
- [Interview Questions](../04-%20Interview%20Questions/)

---

# Key Takeaway

These comparison guides complement the detailed deep-dive notes in the other Database playbook sections. Use them as quick-reference material before interviews, during architecture reviews, or when making production database decisions.

---
