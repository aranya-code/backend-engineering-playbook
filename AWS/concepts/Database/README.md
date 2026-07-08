# AWS Database and Caching Services

A comprehensive, production-focused playbook on AWS database and caching services designed for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and Solution Architects.

This playbook covers everything from core database theory to managed AWS services, caching architectures, production operations, security, scaling, cost optimization, and real-world interview preparation.

---

# What You Will Learn

By completing this playbook, you will understand:

- Core Database Theory (SQL vs NoSQL, ACID, BASE, CAP Theorem)
- Data Organization (Indexing, Normalization, Partitioning, Sharding)
- Database Reliability (Replication, Backups, HA, Disaster Recovery)
- Amazon RDS Architecture and Operations
- Amazon Aurora Architecture and Scaling
- Amazon ElastiCache (Redis and Memcached)
- Amazon MemoryDB for Redis
- Caching Patterns and Failure Mitigations
- Database Security and Encryption
- Monitoring and Performance Tuning
- Cost Optimization Strategies
- Production Troubleshooting
- System Design with Databases
- Senior-Level Interview Preparation

---

# Playbook Structure

```text
Database/
│
├── README.md                          ← You are here
├── Folder Structure.md
├── Quick_Revision_Notes.md
│
├── 00- Fundamentals/                  18 files – Core database theory
│   ├── README.md
│   ├── 01- SQL vs NoSQL.md
│   ├── ...
│   └── 18- Database Design Best Practices.md
│
├── 01- Amazon RDS/                    9 files – Relational database operations
│   ├── README.md
│   ├── 01- Overview and Architecture.md
│   ├── ...
│   └── 09- Best Practices and Cost Optimization.md
│
├── 02- Amazon ElastiCache/            7 files – In-memory caching operations
│   ├── README.md
│   ├── 01- Overview and Caching Patterns.md
│   ├── ...
│   └── 07- Best Practices and MemoryDB.md
│
├── 03- Comparison Guide/              9 files – Side-by-side trade-off analysis
│   ├── README.md
│   ├── 01- RDS vs Database on EC2.md
│   ├── ...
│   └── 09- Partitioning vs Sharding.md
│
└── 04- Interview Questions/           6 files – 42 senior-level Q&A
    ├── README.md
    ├── 01- Relational and NoSQL.md
    ├── ...
    └── 06- Production Troubleshooting Scenarios.md
```

---

# Module Directory

| Directory | Files | Description |
|-----------|-------|-------------|
| 📂 [00- Fundamentals](./00-%20Fundamentals/) | 18 | Core database theory: SQL/NoSQL, CAP, ACID, indexing, sharding, replication, HA, DR |
| 📂 [01- Amazon RDS](./01-%20Amazon%20RDS/) | 9 | RDS architecture, storage, Multi-AZ, replicas, proxy, security, monitoring, cost |
| 📂 [02- Amazon ElastiCache](./02-%20Amazon%20ElastiCache/) | 7 | Caching patterns, Redis vs Memcached, clusters, eviction, failure modes, MemoryDB |
| 📂 [03- Comparison Guide](./03-%20Comparison%20Guide/) | 9 | Side-by-side comparisons for rapid decision-making and interview prep |
| 📂 [04- Interview Questions](./04-%20Interview%20Questions/) | 6 | 42 senior-level questions with detailed model answers and diagrams |

---

# Learning Path

## Phase 1 – Database Foundations

- Database Fundamentals (SQL vs NoSQL, ACID, BASE, CAP)
- Data Organization (Indexing, Normalization, Partitioning, Sharding)
- Reliability (Replication, Backups, HA, Disaster Recovery)

## Phase 2 – AWS Managed Services

- Amazon RDS (Architecture, Storage, Multi-AZ, Read Replicas)
- Amazon RDS (Security, Backups, Proxy, Monitoring, Cost)
- Amazon ElastiCache (Caching Patterns, Redis vs Memcached, Clusters)

## Phase 3 – Advanced Operations

- Cache Failure Mitigations (Stampede, Penetration, Avalanche)
- ElastiCache Security and Monitoring (EngineCPUUtilization)
- Amazon MemoryDB vs ElastiCache

## Phase 4 – Decision Making

- Comparison Guides (9 side-by-side trade-off analyses)
- Database Selection Guide

## Phase 5 – Interview & Real World

- Interview Questions (42 Q&A across 6 categories)
- Production Troubleshooting Scenarios

---

# Architecture Overview

Typical production database tier utilizing caching, read scaling, and multi-AZ failover:

```text
                               Application Server
                                       │
                    ┌──────────────────┴──────────────────┐
                    │ (Reads & Writes)                    │ (High-Throughput Reads)
                    ▼                                     ▼
        ┌──────────────────────┐              ┌──────────────────────┐
        │  RDS Proxy (Pooling) │              │ ElastiCache (Redis)  │
        └──────────┬───────────┘              │ (Sub-ms Cache Tier)  │
                   │                          └──────────────────────┘
                   ▼
┌──────────────────────────────────────┐
│       VPC Private Database Subnets   │
│                                      │
│  ┌────────────────────────────────┐  │
│  │   Primary DB Instance (AZ-1)   │  │
│  │   (Active - Processes Writes)  │  │
│  └───────────────┬────────────────┘  │
│                  │                   │
│     Synchronous  │   Asynchronous    │
│     Replication  │   Replication     │
│                  │                   │
│  ┌───────────────▼───┐  ┌───────────▼────────────┐  │
│  │ Standby (AZ-2)    │  │ Read Replica (AZ-3)    │  │
│  │ (Passive - HA)    │  │ (Active - Read Scale)  │  │
│  └───────────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

# Database Selection Decision Tree

```text
Does the workload require complex SQL JOINs and ACID transactions?
   ├── YES → Need max scale and fast failover?
   │           ├── YES → Amazon Aurora
   │           └── NO  → Amazon RDS
   └── NO
        │
Need millisecond key-value lookups at massive scale?
   ├── YES → Amazon DynamoDB
   └── NO
        │
Need MongoDB-compatible document storage?
   ├── YES → Amazon DocumentDB
   └── NO
        │
Need graph relationship modeling?
   ├── YES → Amazon Neptune
   └── NO
        │
Need sub-millisecond in-memory caching?
   ├── YES → Need durability (RPO=0)?
   │           ├── YES → Amazon MemoryDB
   │           └── NO  → Amazon ElastiCache
   └── NO
        │
Need petabyte-scale analytics?
   └── YES → Amazon Redshift
```

---

# Core AWS Services Covered

```text
Amazon RDS              Amazon Aurora           Amazon ElastiCache
Amazon MemoryDB         Amazon DynamoDB         Amazon Redshift
AWS KMS                 AWS Secrets Manager     AWS IAM
Amazon CloudWatch       Performance Insights    Enhanced Monitoring
Amazon S3 (Backups)     AWS DMS                 Amazon Route 53
```

---

# Key Takeaway

Modern cloud architectures use **polyglot persistence** — selecting the right database for each workload rather than forcing all data into a single engine. This playbook equips you with the knowledge to make those decisions, operate databases at production scale, and defend your choices in technical interviews.

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**