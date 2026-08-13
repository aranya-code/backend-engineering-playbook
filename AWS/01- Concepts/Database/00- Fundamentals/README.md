# Database Fundamentals

A comprehensive reference on core database theory and engineering principles. These notes cover the foundational concepts that every senior backend and DevOps engineer must understand before working with any database system — relational or non-relational, on-premises or cloud-managed.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [SQL vs NoSQL](./01-%20SQL%20vs%20NoSQL.md) | Relational vs non-relational, data modeling philosophy, query-first vs model-first |
| 02 | [OLTP vs OLAP](./02-%20OLTP%20vs%20OLAP.md) | Row vs column storage, transactional vs analytical workloads, ETL pipelines |
| 03 | [CAP Theorem](./03-%20CAP%20Theorem.md) | Consistency, Availability, Partition Tolerance, CP vs AP, PACELC extension |
| 04 | [ACID Properties](./04-%20ACID%20Properties.md) | Atomicity, Consistency, Isolation levels, Durability, WAL, crash recovery |
| 05 | [BASE Model](./05-%20BASE%20Model.md) | Basically Available, Soft State, Eventually Consistent, ACID vs BASE |
| 06 | [Consistency Models](./06-%20Consistency%20Models.md) | Strong, Eventual, Read-After-Write, Causal, Session consistency |
| 07 | [Database Indexing](./07-%20Database%20Indexing.md) | B-Tree internals, composite indexes, covering indexes, EXPLAIN ANALYZE |
| 08 | [Database Normalization](./08-%20Database%20Normalization.md) | 1NF, 2NF, 3NF, BCNF, dependency elimination, when to stop |
| 09 | [Database Denormalization](./09-%20Database%20Denormalization.md) | Materialized views, embedded data, read optimization, trade-offs |
| 10 | [Database Partitioning](./10-%20Database%20Partitioning.md) | Range, list, hash partitioning, partition pruning, hot partitions |
| 11 | [Database Sharding](./11-%20Database%20Sharding.md) | Shard key selection, consistent hashing, cross-shard queries, resharding |
| 12 | [Replication](./12-%20Replication.md) | Sync vs async, single-leader, multi-leader, leaderless, split-brain |
| 13 | [Backup & Recovery](./13-%20Backup%20%26%20Recovery.md) | Full vs incremental, PITR, WAL archiving, RPO/RTO, 3-2-1 rule |
| 14 | [High Availability](./14-%20High%20Availability.md) | Active-passive, active-active, SPOF, SLA calculations, failover |
| 15 | [Disaster Recovery](./15-%20Disaster%20Recovery.md) | DR tiers (Backup & Restore → Multi-Site), RPO/RTO, region failover |
| 16 | [Database Selection Guide](./16-%20Database%20Selection%20Guide.md) | AWS service decision tree, polyglot persistence, service comparison |
| 17 | [SQL Performance Optimization](./17-%20SQL%20Performance%20Optimization.md) | EXPLAIN plans, index tuning, vacuum, connection pooling, query rewriting |
| 18 | [Database Design Best Practices](./18-%20Database%20Design%20Best%20Practices.md) | Schema design, naming conventions, migrations, expand-contract pattern |

---

# Learning Path

```text
Phase 1: Core Theory
  SQL vs NoSQL → OLTP vs OLAP → CAP Theorem → ACID → BASE → Consistency Models

Phase 2: Data Organization
  Indexing → Normalization → Denormalization → Partitioning → Sharding

Phase 3: Reliability
  Replication → Backup & Recovery → High Availability → Disaster Recovery

Phase 4: Applied Engineering
  Database Selection Guide → SQL Performance Optimization → Design Best Practices
```

---

# Who Should Read This?

These fundamentals are database-engine agnostic and apply equally to PostgreSQL, MySQL, DynamoDB, Redis, and any other database system. They are essential reading before diving into the AWS-specific RDS, ElastiCache, and Comparison Guide sections.

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Database Module](../README.md) |
| ➡️ Next | [Amazon RDS](../01-%20Amazon%20RDS/) |

---
