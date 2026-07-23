# 24 - DynamoDB Architecture Deep Dive

## Overview

Most developers interact with DynamoDB through simple API calls such as:

- PutItem
- GetItem
- Query
- UpdateItem
- DeleteItem

These APIs appear deceptively simple.

```text
Application

↓

GetItem()

↓

Response
```

However, behind every request is a globally distributed storage system designed to:

- Handle millions of requests per second
- Scale without downtime
- Replicate data automatically
- Recover from hardware failures
- Deliver single-digit millisecond latency

Understanding DynamoDB's internal architecture helps explain **why certain design principles exist**, such as:

- High-cardinality partition keys
- Access-pattern-based design
- Hot partition avoidance
- Adaptive Capacity
- Eventually consistent reads

This chapter explores DynamoDB from an architectural perspective rather than an API perspective.

---

# High-Level Architecture

A simplified view of DynamoDB looks like this:

```text
                Application

                     │

                     ▼

              DynamoDB API

                     │

                     ▼

          Request Routing Layer

                     │

                     ▼

          Partition Management

                     │

                     ▼

          Storage Partitions

                     │

                     ▼

       Replication & Persistence
```

Each layer has a specific responsibility.

---

# Request Lifecycle

Suppose an application executes:

```text
GetItem(USER#1001)
```

Internally:

```text
Application

↓

API Endpoint

↓

Authentication

↓

Authorization

↓

Hash Partition Key

↓

Locate Partition

↓

Read Item

↓

Return Response
```

This process typically completes within a few milliseconds.

---

# Partition-Based Architecture

Unlike relational databases that organize data into pages or blocks, DynamoDB organizes data into **partitions**.

```text
              DynamoDB Table

        +-------------------------+

        |                         |

        +-------------------------+

             │     │     │

             ▼     ▼     ▼

            P1    P2    P3
```

Each partition stores:

- Items
- Indexes
- Throughput allocation
- Replicas

Partitions are the fundamental scaling unit of DynamoDB.

---

# Hashing

When an item is written:

```text
Partition Key

↓

Hash Function

↓

Partition
```

Example:

```text
USER#1001

↓

Hash()

↓

Partition 7
```

Every future request for:

```text
USER#1001
```

is routed directly to the same partition.

Applications never know which physical partition stores the data.

---

# Why Hashing Matters

Suppose partition keys are:

```text
UserId
```

Millions of unique users produce:

```text
Hash()

↓

Even Distribution
```

Suppose the partition key is:

```text
Country
```

Most users belong to:

```text
USA
```

Hashing cannot compensate for poor key diversity.

Result:

```text
Hot Partition
```

Good partition key design remains critical.

---

# Partition Splitting

As tables grow, DynamoDB automatically creates additional partitions.

Example:

Initial table:

```text
Table

↓

Partition 1
```

Traffic increases.

```text
Partition 1

↓

Split
```

Result:

```text
Partition 1

Partition 2
```

Applications continue operating without interruption.

Scaling occurs transparently.

---

# Adaptive Partition Management

Partition growth is automatic.

AWS continuously evaluates:

- Storage utilization
- Read throughput
- Write throughput
- Traffic distribution

When necessary:

```text
Create New Partition

↓

Redistribute Data

↓

Continue Serving Requests
```

Applications never perform manual sharding.

---

# Request Routing

Applications never specify:

```text
Partition 17
```

Instead:

```text
Partition Key

↓

Hash Function

↓

Routing Layer

↓

Correct Storage Node
```

Routing decisions occur automatically.

---

# Storage Replication

Every partition is replicated across multiple Availability Zones.

Conceptually:

```text
Partition

↓

Replica A

Replica B

Replica C
```

If one storage node fails:

```text
Replica

↓

Continue Serving Data
```

Replication provides:

- Durability
- High availability
- Fault tolerance

---

# Write Workflow

A write request follows this general path:

```text
Application

↓

PutItem

↓

Authentication

↓

Authorization

↓

Locate Partition

↓

Write Leader

↓

Replicate

↓

Commit

↓

Success
```

Only after successful replication does DynamoDB acknowledge the write.

This contributes to its durability guarantees.

---

# Read Workflow

Read requests depend on consistency settings.

### Strongly Consistent Read

```text
Application

↓

Leader Replica

↓

Latest Data
```

---

### Eventually Consistent Read

```text
Application

↓

Nearest Available Replica

↓

Possibly Slightly Older Data
```

Eventually consistent reads improve throughput because multiple replicas can serve requests.

---

# Secondary Indexes

Indexes are stored separately from the base table.

```text
Main Table

↓

Item

↓

Index Update

↓

GSI Storage
```

Each write may also update one or more indexes.

This explains why GSIs consume additional write capacity.

---

# Capacity Allocation

Capacity is assigned at the partition level.

Example:

```text
Table

↓

Partition A

↓

Capacity
```

```text
Partition B

↓

Capacity
```

Uneven traffic causes:

```text
Partition A

↓

Throttling
```

even if:

```text
Partition B

↓

Idle
```

This is why hot partitions occur.

---

# Adaptive Capacity

Suppose one partition suddenly becomes busy.

```text
Partition

↓

Traffic Spike
```

Adaptive Capacity reallocates internal resources.

```text
Additional Capacity

↓

Busy Partition
```

This reduces throttling while maintaining overall table performance.

---

# Storage Engine

Although AWS does not publicly document every implementation detail, DynamoDB's storage engine is optimized for:

- SSD-based storage
- Automatic replication
- Log-structured writes
- Horizontal scalability
- Low-latency retrieval

These design choices enable predictable performance at massive scale.

---

# Failure Handling

Suppose a storage node fails.

```text
Storage Node

↓

Failure
```

Because replicas already exist:

```text
Replica

↓

Becomes Active

↓

Application Continues
```

Applications typically remain unaware of the failure.

---

# Global Tables Architecture

With Global Tables:

```text
Virginia

↓

Replication

↓

Frankfurt

↓

Replication

↓

Tokyo
```

Each region contains a complete copy of the table.

Replication occurs asynchronously between regions.

---

# Internal Components Summary

```text
Client

↓

Authentication

↓

Authorization

↓

API Layer

↓

Request Router

↓

Partition Manager

↓

Storage Partition

↓

Replication

↓

Persistent Storage
```

Each layer contributes to DynamoDB's scalability and reliability.

---

# Why DynamoDB Scales So Well

Traditional databases often scale by upgrading hardware.

```text
Bigger Server

↓

More CPU

↓

More RAM
```

This approach has limits.

DynamoDB scales by:

```text
More Traffic

↓

More Partitions

↓

More Storage Nodes

↓

More Capacity
```

Horizontal scaling allows virtually unlimited growth.

---

# Real-World Example

Imagine Amazon Prime Day.

Traffic increases from:

```text
50,000 Requests/sec
```

to:

```text
5 Million Requests/sec
```

Internally:

```text
Additional Partitions

↓

Adaptive Capacity

↓

Automatic Routing

↓

Replication

↓

Application Continues Running
```

No database administrator manually repartitions the table.

---

# Best Practices

- Design high-cardinality partition keys.
- Understand that partitions—not tables—consume throughput.
- Avoid hot partitions.
- Monitor CloudWatch metrics.
- Minimize unnecessary GSIs.
- Design around access patterns rather than relational schemas.
- Enable Auto Scaling for production workloads.

---

# Common Mistakes

## Thinking of DynamoDB as a Traditional Database

There is no concept of:

- Pages
- Joins
- Buffer pools
- Manual indexes
- Storage engines you manage

AWS abstracts these responsibilities.

---

## Assuming Table Capacity Is Shared Equally

Capacity is enforced at the partition level.

One busy partition can throttle while others remain idle.

---

## Ignoring Internal Architecture

Many DynamoDB design problems arise from misunderstanding how requests are routed and partitions are managed.

Understanding the architecture leads to better schema design.

---

# Architecture Perspective

Complete request flow:

```text
Application

↓

IAM Authentication

↓

IAM Authorization

↓

DynamoDB API

↓

Hash Partition Key

↓

Partition Router

↓

Storage Partition

↓

Leader Replica

↓

Replica Synchronization

↓

Persistent Storage

↓

Response
```

This architecture allows DynamoDB to provide:

- Automatic scaling
- High availability
- Fault tolerance
- Low latency
- Fully managed operations

without requiring database administration.

---

# Interview Notes

A common interview question is:

> **How does DynamoDB know which partition contains an item?**

DynamoDB applies a hash function to the partition key. The resulting hash determines the physical partition responsible for storing that item. Every future request using the same partition key follows the same routing logic.

Another common question is:

> **Why are high-cardinality partition keys so important?**

Because partitions are the unit of storage and throughput. High-cardinality keys distribute requests evenly across many partitions, enabling horizontal scaling. Low-cardinality keys concentrate traffic on a few partitions, creating hot partitions and throttling.

A senior engineer should be able to connect partition keys, hashing, partitions, Adaptive Capacity, Auto Scaling, and request routing into one coherent explanation of how DynamoDB scales internally.

---

# Key Takeaways

- DynamoDB is a distributed, partition-based database designed for horizontal scalability.
- Every request is routed by hashing the partition key.
- Partitions are automatically created, split, and managed by AWS.
- Each partition is replicated across multiple Availability Zones for durability and availability.
- Throughput is enforced at the partition level, making good partition key design essential.
- Adaptive Capacity, Auto Scaling, and partition management work together to maintain performance under changing workloads.
- Understanding DynamoDB's internal architecture is the foundation for designing scalable, production-grade data models.