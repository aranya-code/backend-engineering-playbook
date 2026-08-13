# 02 - NoSQL Fundamentals

## Overview

Before understanding DynamoDB, it is essential to understand **NoSQL**. DynamoDB is not simply a database that stores JSON documents—it belongs to an entirely different family of databases that were designed to solve problems traditional relational databases struggle with at internet scale.

The term **NoSQL** does **not** mean "No SQL." Instead, it stands for **Not Only SQL**, indicating that relational databases are no longer the only solution for modern applications.

NoSQL databases sacrifice certain relational capabilities in exchange for scalability, flexibility, availability, and predictable performance.

Understanding these trade-offs is fundamental to designing efficient DynamoDB data models.

---

# Why Traditional Databases Began to Struggle

Relational databases have powered enterprise applications for decades.

Their strengths include:

- Strong consistency
- ACID transactions
- Complex SQL queries
- JOIN operations
- Normalized data models
- Referential integrity

These capabilities make relational databases excellent for applications such as banking systems, ERP software, CRM platforms, and financial reporting.

However, the internet changed application requirements dramatically.

Modern applications generate:

- Millions of users
- Billions of records
- Continuous writes
- Global traffic
- Unpredictable traffic spikes
- Always-on availability requirements

These workloads expose several limitations of relational databases.

---

## The Scaling Problem

Suppose an online shopping platform starts with a single PostgreSQL database.

```text
                Application
                     │
                     ▼
             PostgreSQL Server
```

Initially, this architecture performs well.

As traffic grows, the database becomes the bottleneck.

The first solution is usually to upgrade the server.

```text
4 CPU
   │
   ▼
8 CPU
   │
   ▼
32 CPU
   │
   ▼
128 CPU
```

Eventually this approach becomes:

- Expensive
- Difficult to maintain
- Limited by hardware
- Difficult to upgrade without downtime

This is known as **Vertical Scaling**.

---

## Horizontal Scaling

Instead of building a larger server, distributed systems add more servers.

```text
            Database Cluster

     ┌────────┬────────┬────────┐
     │ Node 1 │ Node 2 │ Node 3 │
     └────────┴────────┴────────┘
```

Each server stores part of the overall dataset.

Advantages include:

- Nearly unlimited scalability
- Better fault tolerance
- Lower infrastructure costs
- Higher availability

This is called **Horizontal Scaling**.

DynamoDB was designed around this principle.

---

# What Makes a Database Distributed?

A distributed database stores its data across multiple physical machines.

Instead of one server storing every record:

```text
User 1  → Server A

User 2  → Server B

User 3  → Server C

User 4  → Server D
```

The application still views the system as **one database**.

The complexity of locating data is handled internally.

Distributed databases must solve problems that single-server databases never encounter:

- Data partitioning
- Replication
- Synchronization
- Network failures
- Load balancing
- Failover

DynamoDB automates all of these responsibilities.

---

# What is NoSQL?

NoSQL is a category of databases built around distributed architectures rather than relational models.

Unlike SQL databases, NoSQL systems are designed to prioritize:

- Scalability
- Availability
- Flexibility
- Performance

Instead of storing information in fixed tables with predefined columns, NoSQL databases support more flexible data structures.

---

# Types of NoSQL Databases

NoSQL databases are generally divided into four categories.

## Key-Value Databases

Store information as a simple key and value.

```text
User123

↓

{
 Name,
 Email,
 Country
}
```

Examples:

- Amazon DynamoDB
- Redis
- Riak

Best suited for:

- Session storage
- Shopping carts
- User profiles
- Authentication

---

## Document Databases

Documents contain structured information, typically JSON.

Example:

```json
{
  "productId": 100,
  "name": "Laptop",
  "price": 900,
  "category": "Electronics"
}
```

Examples:

- MongoDB
- Couchbase

Ideal for applications where records contain varying fields.

---

## Wide Column Databases

Instead of storing fixed rows, these databases organize data into column families.

Examples:

- Apache Cassandra
- Google Bigtable

Designed for:

- Massive datasets
- Time-series workloads
- Analytics
- IoT

---

## Graph Databases

Designed to model relationships.

Example:

```text
Alice

│

Friend

│

Bob

│

Purchased

│

Laptop
```

Examples:

- Neo4j
- Amazon Neptune

Ideal for:

- Social networks
- Fraud detection
- Recommendation engines
- Network topology

---

# Where Does DynamoDB Fit?

DynamoDB combines characteristics of both:

- Key-Value databases
- Document databases

Each item is uniquely identified by a primary key but can also contain nested documents, lists, maps, and sets.

This combination makes DynamoDB flexible enough for most cloud-native applications.

---

# SQL vs NoSQL

| Feature | SQL | NoSQL |
|----------|------|--------|
| Schema | Fixed | Flexible |
| Joins | Supported | Limited |
| Scaling | Vertical | Horizontal |
| Data Model | Relational | Multiple Models |
| Availability | Moderate | Very High |
| Latency | Depends on workload | Predictable |
| Infrastructure | Often self-managed | Usually distributed |

Neither model is universally better.

Each solves different engineering problems.

---

# ACID vs BASE

Relational databases emphasize **ACID** guarantees.

| Property | Meaning |
|-----------|----------|
| Atomicity | All operations succeed or fail together |
| Consistency | Database remains valid |
| Isolation | Transactions do not interfere |
| Durability | Committed data is never lost |

NoSQL systems generally emphasize **BASE**.

| Property | Meaning |
|-----------|----------|
| Basically Available | System remains operational |
| Soft State | Data may temporarily differ across replicas |
| Eventually Consistent | Replicas synchronize over time |

This does **not** mean NoSQL databases cannot support transactions.

For example, DynamoDB provides full ACID transactions while still operating as a distributed database.

The important distinction is that distributed systems often optimize for availability and scalability first.

---

# CAP Theorem

One of the most important concepts in distributed systems is the **CAP Theorem**.

It states that during a network partition, a distributed database can guarantee only two of the following three properties.

- Consistency
- Availability
- Partition Tolerance

```text
          Consistency
                ▲
               / \
              /   \
             /     \
Availability-------Partition Tolerance
```

Since network failures are inevitable, every distributed database must support **Partition Tolerance**.

The remaining design choice becomes balancing:

- Consistency
- Availability

Different databases make different trade-offs.

---

# DynamoDB's Design Choice

DynamoDB prioritizes:

- High Availability
- Partition Tolerance

By default, read operations are **Eventually Consistent**, allowing the system to remain highly available while synchronizing replicas in the background.

For applications requiring the latest committed value, DynamoDB also supports **Strongly Consistent Reads**.

This flexibility allows developers to choose between lower latency and stronger consistency depending on business requirements.

---

# Engineering Trade-offs

Every database makes trade-offs.

DynamoDB intentionally sacrifices:

- JOIN operations
- Complex SQL queries
- Relational constraints

In return, it provides:

- Automatic horizontal scaling
- Multi-AZ replication
- Extremely low latency
- Automatic partition management
- Managed infrastructure
- Virtually unlimited throughput

These trade-offs explain why DynamoDB excels at high-scale operational workloads but is not suitable for analytical reporting or heavily relational applications.

---

# Key Takeaways

- NoSQL databases were created to solve scalability and availability challenges that traditional relational databases encounter at large scale.
- Horizontal scaling is the foundation of distributed databases.
- DynamoDB combines the characteristics of key-value and document databases.
- Understanding ACID, BASE, and the CAP Theorem is essential for understanding DynamoDB's architecture.
- DynamoDB intentionally trades relational flexibility for predictable performance, scalability, and operational simplicity.
- Choosing between SQL and NoSQL is an architectural decision based on workload requirements rather than a question of which technology is "better."