# Amazon DynamoDB

Amazon DynamoDB is AWS's fully managed NoSQL database service designed to deliver **single-digit millisecond latency** at virtually any scale. Unlike traditional relational databases, DynamoDB is built around **horizontal scalability**, **partition-based storage**, and **access-pattern-driven data modeling**, making it one of the most widely used databases for cloud-native applications.

These notes are designed for **Senior Backend Developers**, **System Design interviews**, and **AWS professional engineers**. Instead of focusing only on AWS certification topics, they explain the engineering principles behind DynamoDB, internal architecture, production design decisions, and real-world trade-offs.

---

# Learning Objectives

After completing these notes, you will understand:

- DynamoDB architecture and internal design
- NoSQL fundamentals
- Data modeling philosophy
- Partitioning and scaling
- Read and write consistency
- Capacity planning
- CRUD operations
- Performance optimization
- Transactions
- Streams
- Global Tables
- Security
- Disaster recovery
- Production best practices

---

# Prerequisites

Before starting DynamoDB, you should be familiar with:

- Basic database concepts
- SQL fundamentals
- REST APIs
- AWS IAM basics
- Basic cloud computing concepts

No prior NoSQL experience is required.

---

# Folder Structure

```text
Amazon DynamoDB
│
├── 01- Concepts
│   ├── 01- Introduction.md
│   ├── 02- NoSQL Fundamentals.md
│   ├── 03- Tables, Items and Attributes.md
│   ├── 04- Data Types.md
│   ├── 05- Primary Keys.md
│   ├── 06- Partition Keys and Sort Keys.md
│   ├── 07- Partitions and Data Distribution.md
│   ├── 08- Read Consistency Models.md
│   ├── 09- Read Capacity Units (RCU) and Write Capacity Units (WCU).md
│   ├── 10- Capacity Modes.md
│   ├── 11- CRUD Operations.md
│   ├── 12- Adaptive Capacity.md
│   ├── 13- Hot Partitions.md
│   ├── 14- Auto Scaling.md
│   ├── 15- DynamoDB Accelerator (DAX).md
│   ├── 16- Streams.md
│   ├── 17- Time To Live (TTL).md
│   ├── 18- Transactions.md
│   ├── 19- Global Tables.md
│   ├── 20- PartiQL.md
│   ├── 21- Backup, Restore and Export.md
│   ├── 22- Security and Encryption.md
│   ├── 23- Point-in-Time Recovery (PITR).md
│   ├── 24- DynamoDB Architecture Deep Dive.md
│   └── 25- Best Practices and Anti-Patterns.md

```

> **Note:** This README covers the **Concepts** section. Additional folders such as Data Modeling, Secondary Indexes, CLI, Troubleshooting, and Interview Questions can be completed independently.

---

# Quick Navigation

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction](./01-%20Introduction.md) | Learn what Amazon DynamoDB is, why it exists, its core architecture, and how it differs from traditional relational databases. |
| [02 - NoSQL Fundamentals](./02-%20NoSQL%20Fundamentals.md) | Understand NoSQL concepts, CAP theorem, eventual consistency, and why DynamoDB is a key-value/document database. |
| [03 - Tables, Items and Attributes](./03-%20Tables,%20Items%20and%20Attributes.md) | Learn the core building blocks of DynamoDB including tables, items, attributes, and schema flexibility. |
| [04 - Data Types](./04-%20Data%20Types.md) | Explore DynamoDB scalar, document, and set data types along with serialization and storage considerations. |
| [05 - Primary Keys](./05-%20Primary%20Keys.md) | Learn simple and composite primary keys, uniqueness, and how primary keys determine data access. |
| [06 - Partition Keys and Sort Keys](./06-%20Partition%20Keys%20and%20Sort%20Keys.md) | Understand partition key selection, composite keys, sorting, and efficient query patterns. |
| [07 - Partitions and Data Distribution](./07-%20Partitions%20and%20Data%20Distribution.md) | Learn how DynamoDB distributes data across partitions, partition splitting, and scaling mechanisms. |
| [08 - Read Consistency Models](./08-%20Read%20Consistency%20Models.md) | Understand strong consistency, eventual consistency, and when each consistency model should be used. |
| [09 - Read Capacity Units (RCU) and Write Capacity Units (WCU)](./09-%20Read%20Capacity%20Units%20(RCU)%20and%20Write%20Capacity%20Units%20(WCU).md) | Learn how DynamoDB measures throughput, calculates capacity consumption, and handles reads and writes. |
| [10 - Capacity Modes](./10-%20Capacity%20Modes.md) | Compare Provisioned and On-Demand capacity modes, auto scaling, and workload optimization. |
| [11 - CRUD Operations](./11-%20CRUD%20Operations.md) | Master Create, Read, Update, and Delete operations using DynamoDB APIs and best practices. |
| [12 - Adaptive Capacity](./12-%20Adaptive%20Capacity.md) | Learn how Adaptive Capacity automatically balances throughput to reduce hot partition issues. |
| [13 - Hot Partitions](./13-%20Hot%20Partitions.md) | Understand why hot partitions occur, how they impact performance, and strategies to prevent them. |
| [14 - Auto Scaling](./14-%20Auto%20Scaling.md) | Learn how DynamoDB Auto Scaling adjusts provisioned throughput automatically based on demand. |
| [15 - DynamoDB Accelerator (DAX)](./15-%20DynamoDB%20Accelerator%20(DAX).md) | Explore DynamoDB Accelerator, in-memory caching, architecture, and performance improvements. |
| [16 - Streams](./16-%20Streams.md) | Learn how DynamoDB Streams capture item-level changes for event-driven architectures and integrations. |
| [17 - Time To Live (TTL)](./17-%20Time%20To%20Live%20(TTL).md) | Understand automatic item expiration, lifecycle management, and cost optimization using TTL. |
| [18 - Transactions](./18-%20Transactions.md) | Learn ACID transactions in DynamoDB, transactional APIs, and multi-item consistency. |
| [19 - Global Tables](./19-%20Global%20Tables.md) | Explore multi-region replication, disaster recovery, and globally distributed DynamoDB deployments. |
| [20 - PartiQL](./20-%20PartiQL.md) | Learn how PartiQL provides SQL-like querying capabilities for DynamoDB while retaining NoSQL scalability. |
| [21 - Backup, Restore and Export](./21-%20Backup,%20Restore%20and%20Export.md) | Understand backup strategies, point-in-time recovery, exports, and disaster recovery planning. |
| [22 - Security and Encryption](./22-%20Security%20and%20Encryption.md) | Learn IAM integration, encryption at rest, encryption in transit, KMS, and security best practices. |
| [23 - Point-in-Time Recovery (PITR)](./23-%20Point-in-Time-Recovery%20(PITR).md) | Explore continuous backups, recovery windows, and restoring tables to specific points in time. |
| [24 - DynamoDB Architecture Deep Dive](./24-%20DynamoDB%20Architecture%20Deep%20Dive.md) | Understand DynamoDB internals including partition management, request routing, replication, and scaling architecture. |
| [25 - Best Practices and Anti-Patterns](./25-%20Best%20Practices%20and%20Anti-Patterns.md) | Learn production best practices, common design mistakes, optimization techniques, and architectural recommendations for DynamoDB. |

---

# Learning Path

```text
Introduction
      │
      ▼
NoSQL Fundamentals
      │
      ▼
Core Concepts
(Tables, Keys, Partitions)
      │
      ▼
Capacity Planning
      │
      ▼
CRUD Operations
      │
      ▼
Performance & Scaling
      │
      ▼
Advanced Features
      │
      ▼
Security
      │
      ▼
Architecture
      │
      ▼
Production Best Practices
```

---

# Who Should Read These Notes?

These notes are ideal for:

- Senior Backend Developers
- Python / Java / Go Developers
- Cloud Engineers
- AWS Developers
- DevOps Engineers
- Solutions Architects
- Technical Leads
- Software Engineering Interview Candidates

---

# Key Features of These Notes

- Senior backend engineering perspective
- Internal architecture explanations
- Production-ready examples
- System design insights
- AWS best practices
- Performance optimization techniques
- Security recommendations
- Cost optimization strategies
- Interview-focused discussions
- Architecture diagrams
- Real-world engineering trade-offs

---


# License

These notes are intended for educational purposes and backend engineering interview preparation.