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

| Chapter | Topic |
|----------|-------|
| [01 - Introduction](./01-%20Concepts/01-%20Introduction.md) | Learn what DynamoDB is, why it exists, and where it fits in modern cloud architectures. |
| [02 - NoSQL Fundamentals](./01-%20Concepts/02-%20NoSQL%20Fundamentals.md) | Understand NoSQL databases, CAP theorem, horizontal scaling, and why DynamoDB is different from relational databases. |
| [03 - Tables, Items and Attributes](./01-%20Concepts/03-%20Tables,%20Items%20and%20Attributes.md) | Learn the fundamental building blocks of DynamoDB and flexible schema design. |
| [04 - Data Types](./01-%20Concepts/04-%20Data%20Types.md) | Explore scalar, document, and set data types supported by DynamoDB. |
| [05 - Primary Keys](./01-%20Concepts/05-%20Primary%20Keys.md) | Understand simple and composite primary keys and their role in data distribution. |
| [06 - Partition Keys and Sort Keys](./01-%20Concepts/06-%20Partition%20Keys%20and%20Sort%20Keys.md) | Learn how DynamoDB organizes data using partition and sort keys. |
| [07 - Partitions and Data Distribution](./01-%20Concepts/07-%20Partitions%20and%20Data%20Distribution.md) | Discover how DynamoDB partitions data and scales horizontally. |
| [08 - Read Consistency Models](./01-%20Concepts/08-%20Read%20Consistency%20Models.md) | Learn eventual consistency, strong consistency, and replication trade-offs. |
| [09 - Read Capacity Units (RCU) and Write Capacity Units (WCU)](./01-%20Concepts/09-%20Read%20Capacity%20Units%20(RCU)%20and%20Write%20Capacity%20Units%20(WCU).md) | Calculate throughput consumption and understand capacity planning. |
| [10 - Capacity Modes](./01-%20Concepts/10-%20Capacity%20Modes.md) | Compare On-Demand and Provisioned Capacity modes. |
| [11 - CRUD Operations](./01-%20Concepts/11-%20CRUD%20Operations.md) | Master DynamoDB CRUD APIs, conditional writes, and update expressions. |
| [12 - Adaptive Capacity](./01-%20Concepts/12-%20Adaptive%20Capacity.md) | Learn how DynamoDB automatically redistributes capacity to busy partitions. |
| [13 - Hot Partitions](./01-%20Concepts/13-%20Hot%20Partitions.md) | Understand causes, detection, and mitigation strategies for hot partitions. |
| [14 - Auto Scaling](./01-%20Concepts/14-%20Auto%20Scaling.md) | Learn how DynamoDB automatically adjusts throughput based on demand. |
| [15 - DynamoDB Accelerator (DAX)](./01-%20Concepts/15-%20DynamoDB%20Accelerator%20(DAX).md) | Explore DynamoDB's in-memory caching layer for microsecond latency. |
| [16 - Streams](./01-%20Concepts/16-%20Streams.md) | Understand change data capture, event-driven architectures, and Lambda integration. |
| [17 - Time To Live (TTL)](./01-%20Concepts/17-%20Time%20To%20Live%20(TTL).md) | Learn automatic data expiration and lifecycle management. |
| [18 - Transactions](./01-%20Concepts/18-%20Transactions.md) | Explore ACID transactions, optimistic locking, and multi-item consistency. |
| [19 - Global Tables](./01-%20Concepts/19-%20Global%20Tables.md) | Learn active-active multi-region replication and global application design. |
| [20 - PartiQL](./01-%20Concepts/20-%20PartiQL.md) | Query DynamoDB using SQL-like syntax with PartiQL. |
| [21 - Backup, Restore and Export](./01-%20Concepts/21-%20Backup,%20Restore%20and%20Export.md) | Understand backup strategies, disaster recovery, and exporting data to Amazon S3. |
| [22 - Security and Encryption](./01-%20Concepts/22-%20Security%20and%20Encryption.md) | Learn IAM, KMS, encryption, VPC endpoints, and auditing with CloudTrail. |
| [23 - Point-in-Time Recovery (PITR)](./01-%20Concepts/23-%20Point-in-Time%20Recovery%20(PITR).md) | Deep dive into continuous backups, recovery strategies, RPO, and RTO. |
| [24 - DynamoDB Architecture Deep Dive](./01-%20Concepts/24-%20DynamoDB%20Architecture%20Deep%20Dive.md) | Explore DynamoDB internals including partitions, request routing, replication, and storage architecture. |
| [25 - Best Practices and Anti-Patterns](./01-%20Concepts/25-%20Best%20Practices%20and%20Anti-Patterns.md) | Consolidate production recommendations, architectural guidelines, and common mistakes. |

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