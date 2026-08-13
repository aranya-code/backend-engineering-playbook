# Amazon RDS

A comprehensive deep-dive into Amazon Relational Database Service (RDS) — AWS's fully managed relational database platform. These notes cover architecture, storage, high availability, scaling, security, backup, monitoring, and cost optimization from a senior DevOps and backend engineering perspective.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [Overview and Architecture](./01-%20Overview%20and%20Architecture.md) | Control plane vs data plane, managed operations, ENI mapping, supported engines |
| 02 | [Storage and Instance Classes](./02-%20Storage%20and%20Instance%20Classes.md) | gp2 vs gp3 vs io1 vs io2, storage auto-scaling (up only), instance categories |
| 03 | [High Availability and Multi-AZ](./03-%20High%20Availability%20and%20Multi-AZ.md) | Multi-AZ instances vs DB clusters, synchronous replication, failover workflow |
| 04 | [Read Replicas and Scaling](./04-%20Read%20Replicas%20and%20Scaling.md) | Asynchronous replication, replication lag, cross-region replicas, promotion |
| 05 | [Security and Encryption](./05-%20Security%20and%20Encryption.md) | KMS encryption at rest, SSL enforcement, IAM authentication, snapshot migration |
| 06 | [Backups and Restore](./06-%20Backups%20and%20Restore.md) | Automated backups, PITR, manual snapshots, cross-account sharing, KMS re-encryption |
| 07 | [RDS Proxy](./07-%20RDS%20Proxy.md) | Connection pooling, Lambda integration, failover reduction, connection pinning |
| 08 | [Monitoring and Observability](./08-%20Monitoring%20and%20Observability.md) | CloudWatch metrics, Enhanced Monitoring, Performance Insights (AAS), troubleshooting |
| 09 | [Best Practices and Cost Optimization](./09-%20Best%20Practices%20and%20Cost%20Optimization.md) | 7-day stop limit, Reserved Instances, deletion protection, gp3 migration |

---

# Quick Reference

```text
RDS Architecture:

Customer VPC
┌──────────────────────────────────────────────────┐
│  App Subnet            DB Subnet                 │
│  ┌─────────┐          ┌─────────────────────┐    │
│  │ App EC2 │──────────│ ENI → RDS Instance  │    │
│  └─────────┘          │  (Primary, AZ-1)    │    │
│                       └──────────┬──────────┘    │
│                                  │ Sync Repl     │
│                       ┌──────────▼──────────┐    │
│                       │ ENI → RDS Standby   │    │
│                       │  (Passive, AZ-2)    │    │
│                       └─────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## Key Numbers to Remember

| Metric | Value |
|--------|-------|
| Max Read Replicas | 5–15 (engine dependent) |
| Multi-AZ Failover Time | 60–120 seconds (30s with Proxy) |
| Backup Retention | 1–35 days |
| PITR Granularity | 5 minutes |
| Storage Auto Scaling Cooldown | 6 hours |
| Max Storage | 64 TiB |
| IAM Auth Connection Limit | 200 connections/second |

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Database Module](../README.md) |
| ⬅️ Previous | [Fundamentals](../00-%20Fundamentals/) |
| ➡️ Next | [Amazon ElastiCache](../02-%20Amazon%20ElastiCache/) |

---
