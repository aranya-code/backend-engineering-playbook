# 01 - Introduction to Amazon DynamoDB

## Overview

Amazon DynamoDB is a **fully managed, distributed NoSQL database service** designed to deliver **predictable single-digit millisecond latency** regardless of workload size. Unlike traditional databases that require administrators to manage servers, storage, replication, and scaling, DynamoDB abstracts away the underlying infrastructure so that developers can focus entirely on application design and data modeling.

DynamoDB is not simply "a database hosted on AWS." It represents a different approach to database engineering. Rather than optimizing for complex relational queries, it is optimized for applications that demand extremely high throughput, low latency, and continuous availability.

Today, DynamoDB powers workloads that process **millions of requests per second** across industries including e-commerce, financial services, gaming, IoT, SaaS platforms, and real-time analytics.

---

# The Problem DynamoDB Solves

To understand why DynamoDB exists, it is important to understand the limitations of traditional relational databases.

For decades, relational databases such as PostgreSQL, MySQL, Oracle, and SQL Server have been the foundation of enterprise software. They excel at maintaining complex relationships between data, enforcing consistency, and supporting sophisticated SQL queries.

However, internet-scale applications introduced a completely different set of challenges.

Imagine building an e-commerce platform serving customers worldwide.

The application must:

- Handle millions of concurrent users.
- Continue operating even when servers fail.
- Scale automatically during seasonal traffic spikes.
- Serve requests with very low latency.
- Replicate data across multiple data centers.

These requirements expose several limitations of traditional relational databases.

### Vertical Scaling Eventually Stops Working

Most SQL databases scale by upgrading to larger hardware.

```text
4 CPU  →  8 CPU  → 16 CPU → 32 CPU
```

Eventually:

- Larger servers become extremely expensive.
- Hardware limits are reached.
- Database upgrades require downtime.
- A single database server becomes a bottleneck.

This approach is known as **vertical scaling**, and while effective initially, it does not scale indefinitely.

---

### Manual Sharding Introduces Operational Complexity

Once a single database server is no longer sufficient, organizations often split data across multiple servers.

For example:

```text
Customer A–F  → Database 1

Customer G–M  → Database 2

Customer N–Z  → Database 3
```

This process is called **database sharding**.

Although sharding increases capacity, it also introduces significant complexity.

Developers must determine:

- Which database stores each record.
- How queries span multiple shards.
- How to rebalance data as traffic changes.
- How to handle server failures.
- How to migrate data between shards.

Large engineering teams often dedicate entire teams to solving these operational challenges.

AWS wanted developers to never think about sharding again.

---

### High Availability Should Not Be Optional

Modern applications cannot afford prolonged downtime.

If a database server fails, users still expect the application to function.

Traditional databases typically require administrators to configure:

- Replication
- Standby servers
- Automatic failover
- Backup strategies
- Disaster recovery

These systems are powerful but operationally expensive.

DynamoDB was designed with the assumption that hardware failures are inevitable.

Instead of treating failures as exceptional events, it treats them as normal operating conditions.

---

### Low Latency at Massive Scale

As databases grow, query performance often becomes increasingly difficult to maintain.

Indexes become larger.

Storage grows.

Disk I/O increases.

Caching becomes more complicated.

Query planners become more expensive.

DynamoDB was engineered around a different philosophy:

> Response time should remain predictable regardless of dataset size.

Whether a table stores one thousand items or one trillion items, DynamoDB aims to maintain **single-digit millisecond latency** for properly designed workloads.

Predictable performance is one of its defining characteristics.

---

# Evolution of Database Systems

Database technology has evolved alongside application architecture.

```text
Relational Databases
        │
        ▼
Vertical Scaling
        │
        ▼
Manual Sharding
        │
        ▼
Distributed Databases
        │
        ▼
NoSQL Databases
        │
        ▼
Amazon DynamoDB
```

Each stage attempted to solve the scalability limitations of the previous generation.

DynamoDB represents AWS's solution to building databases for cloud-native, internet-scale applications.

Instead of requiring engineers to manage distributed systems manually, AWS provides distributed storage as a managed service.

This shift allows development teams to spend more time building products rather than operating infrastructure.

---

# What Exactly is DynamoDB?

At its core, DynamoDB is a **distributed key-value and document database**.

This definition is important because it describes how DynamoDB stores and retrieves data.

Unlike relational databases, DynamoDB does not organize information around relationships between tables.

Instead, data is organized around **items**, each uniquely identified by a **primary key**.

Internally, DynamoDB automatically distributes items across multiple physical partitions based on that primary key.

Developers never decide:

- Which server stores the data.
- Which disk stores the data.
- How replicas are synchronized.
- When partitions should split.
- How storage expands.

Those responsibilities belong entirely to AWS.

This separation between application logic and infrastructure management is one of DynamoDB's greatest strengths.

---

# Design Philosophy

DynamoDB was designed around several fundamental assumptions.

### Hardware Eventually Fails

Rather than preventing failures, DynamoDB assumes failures will occur continuously.

Servers fail.

Network links fail.

Storage devices fail.

Availability Zones fail.

The system is built to continue operating despite these failures.

---

### Applications Grow Unpredictably

Traffic is rarely constant.

An application may process:

- 100 requests per second today.
- 10,000 tomorrow.
- 1 million during a holiday sale.

Developers should not need to redesign their database architecture every time traffic increases.

---

### Infrastructure Should Be Invisible

Traditional databases require administrators to manage infrastructure.

DynamoDB attempts to eliminate that responsibility.

Developers interact with:

- Tables
- Keys
- Items
- Attributes

AWS manages everything else.

This is the essence of a fully managed database service.

---

# Key Characteristics

DynamoDB combines several architectural principles that distinguish it from traditional databases.

- Distributed by design.
- Fully managed by AWS.
- Horizontally scalable.
- Multi-AZ by default.
- Serverless.
- Low-latency.
- Highly durable.
- Fault tolerant.

These are not individual features—they are consequences of the underlying distributed architecture.

The following chapters explore each of these characteristics in depth.

---

# Key Takeaways

- DynamoDB was built to solve scalability and operational challenges that traditional relational databases encounter at internet scale.
- It is a distributed key-value and document database rather than a relational database.
- AWS automatically manages partitioning, replication, scaling, failover, and infrastructure.
- DynamoDB prioritizes predictable low latency, high availability, and horizontal scalability over complex relational querying.
- Understanding **why DynamoDB was designed this way** is more important than memorizing its features. Nearly every design decision in later chapters—including partition keys, capacity modes, indexes, and single-table design—builds upon these architectural principles.