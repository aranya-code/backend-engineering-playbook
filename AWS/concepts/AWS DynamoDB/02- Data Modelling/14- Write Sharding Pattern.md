# 14 - Write Sharding Pattern

## Overview

One of the biggest performance challenges in DynamoDB is the **Hot Partition Problem**.

DynamoDB automatically distributes data across partitions based on the **Partition Key**.

If too many write requests target the same partition key, that partition becomes overloaded.

This results in:

- Increased latency
- Write throttling
- Reduced throughput
- Poor scalability

The **Write Sharding Pattern** solves this problem by intentionally spreading writes across multiple partition keys.

It is one of the most important techniques for building **high-throughput DynamoDB applications**.

---

# Why Hot Partitions Occur

Consider an IoT application.

Every sensor reading is stored using:

```text
PK = DEVICE#100
```

Thousands of devices are writing:

```text
DEVICE#100
```

Every write targets the same logical partition.

```text
DEVICE#100

↓

Write

↓

Write

↓

Write

↓

Write

↓

Write
```

Eventually:

```text
Hot Partition
```

---

# Real Production Example

Imagine Amazon Prime Day.

Every order for one popular product uses:

```text
PK = PRODUCT#PS6
```

Millions of customers purchase simultaneously.

All writes hit:

```text
PRODUCT#PS6
```

Result:

```text
Throttling
```

---

# DynamoDB Partitions

Internally DynamoDB hashes the Partition Key.

```text
Application

↓

Partition Key

↓

Hash

↓

Physical Partition
```

If every request has the same key:

```text
Same Hash

↓

Same Partition
```

The load cannot be distributed.

---

# The Solution

Instead of one partition key:

```text
DEVICE#100
```

Generate multiple keys.

Example:

```text
DEVICE#100#0

DEVICE#100#1

DEVICE#100#2

DEVICE#100#3
```

Now writes spread across:

```text
Partition A

Partition B

Partition C

Partition D
```

instead of one.

---

# Visual Representation

Without sharding:

```text
DEVICE#100

↓

████████████████

One Busy Partition
```

With sharding:

```text
DEVICE#100#0

↓

████
```

```text
DEVICE#100#1

↓

████
```

```text
DEVICE#100#2

↓

████
```

```text
DEVICE#100#3

↓

████
```

Load becomes balanced.

---

# Random Sharding

One common strategy is random selection.

Possible keys:

```text
DEVICE#100#0

DEVICE#100#1

DEVICE#100#2

DEVICE#100#3
```

Every new write randomly chooses one.

Example:

```python
Shard = Random(0-3)
```

Result:

```text
Balanced Writes
```

---

# Hash-Based Sharding

Instead of randomness:

Compute:

```text
Hash(EventID)

↓

Mod 4

↓

Shard
```

Example:

```text
EventID

↓

Hash

↓

Shard 2
```

Advantages:

- Deterministic
- Even distribution
- Easy replay

---

# Time-Based Sharding

Another option:

Combine sharding with dates.

Example:

```text
PK = DEVICE#100#2026-07-23#0
```

Another:

```text
PK = DEVICE#100#2026-07-23#1
```

Tomorrow:

```text
DEVICE#100#2026-07-24#0
```

Now both:

- Time
- Write load

are distributed.

---

# Example – Banking

Suppose one account processes:

```text
100,000

Transactions/Second
```

Without sharding:

```text
ACCOUNT#500
```

With sharding:

```text
ACCOUNT#500#0

ACCOUNT#500#1

ACCOUNT#500#2

ACCOUNT#500#3
```

Transaction load spreads evenly.

---

# Example – Chat Application

Chat Room:

```text
General
```

Receives:

```text
50,000 Messages

Per Second
```

Instead of:

```text
ROOM#General
```

Use:

```text
ROOM#General#0

ROOM#General#1

ROOM#General#2

ROOM#General#3
```

Message ingestion scales horizontally.

---

# Example – Metrics Collection

Server metrics:

```text
SERVER#100
```

becomes:

```text
SERVER#100#0

SERVER#100#1

SERVER#100#2

SERVER#100#3
```

Cloud monitoring systems commonly use this approach.

---

# Reading Sharded Data

Writing becomes easy.

Reading requires extra work.

Suppose:

```text
4 Shards
```

Application queries:

```text
Shard 0

↓

Shard 1

↓

Shard 2

↓

Shard 3
```

Results are merged.

---

# Read Workflow

```text
Application

↓

Query Shard 0

↓

Query Shard 1

↓

Query Shard 2

↓

Query Shard 3

↓

Merge Results

↓

Return Response
```

Reads become slightly more expensive.

Writes become dramatically more scalable.

---

# Choosing the Number of Shards

Small workloads:

```text
4
```

shards.

Large workloads:

```text
10
```

or

```text
20
```

Very large workloads:

```text
100+
```

Choose based on expected write throughput.

---

# Dynamic Sharding

Some systems begin with:

```text
4 Shards
```

Later:

```text
8

16

32
```

Dynamic shard expansion supports application growth.

Applications must understand which shard ranges exist.

---

# Combining with GSIs

Suppose logs are sharded.

Primary key:

```text
SERVICE#Payment#2
```

Need:

```text
Find

ERROR

Logs
```

Create GSI:

```text
PK = ERROR

SK = Timestamp
```

Applications query:

```text
ERROR

↓

Latest Errors
```

independent of write shards.

---

# Benefits

Write sharding provides:

- Higher write throughput
- Better scalability
- Reduced throttling
- Balanced partitions
- Improved latency

---

# Trade-Offs

Advantages:

- Massive scalability
- Better partition utilization
- Lower throttling

Disadvantages:

- More complex reads
- Result aggregation
- Additional application logic

Like many DynamoDB patterns, this is a deliberate trade-off:

> **Optimize writes by accepting slightly more complex reads.**

---

# Real-World Example

An analytics platform records page views.

Peak traffic:

```text
2 Million Events

Per Minute
```

Instead of:

```text
PAGE#Homepage
```

Use:

```text
PAGE#Homepage#0

PAGE#Homepage#1

PAGE#Homepage#2

PAGE#Homepage#3
```

Traffic spreads across partitions while dashboards aggregate data from all shards.

---

# Best Practices

- Shard only when necessary.
- Start with a reasonable shard count.
- Use deterministic hashing when possible.
- Combine sharding with time bucketing for time-series data.
- Monitor partition metrics using CloudWatch.
- Document shard selection logic clearly.

---

# Common Mistakes

## Sharding Too Early

Many workloads never require write sharding.

Measure traffic before introducing complexity.

---

## Using Too Few Shards

Example:

```text
1 Million Writes

↓

2 Shards
```

Hot partitions may still occur.

---

## Using Too Many Shards

Example:

```text
500 Writes

↓

100 Shards
```

Reads become unnecessarily expensive.

---

## Forgetting Read Aggregation

Applications must query all relevant shards.

Ignoring this results in incomplete datasets.

---

# Architecture Perspective

```text
Application

        │

        ▼

Determine Shard

        │

        ▼

Hash(EventID) % 4

        │

        ▼

DEVICE#100#2

        │

        ▼

DynamoDB Partition

        │

        ▼

Write Successful
```

Instead of overwhelming a single partition, writes are evenly distributed across multiple partitions.

---

# Production Considerations

Large-scale AWS services commonly combine Write Sharding with:

- Time Bucketing
- DynamoDB Streams
- Lambda
- Kinesis
- Amazon S3
- Global Secondary Indexes

This architecture supports ingestion rates of millions of events per second while maintaining predictable performance.

---

# Interview Notes

A common interview question is:

> **What is Write Sharding in DynamoDB?**

Write Sharding is a data modeling technique that distributes writes across multiple partition keys by appending a shard identifier. This prevents hot partitions and improves write scalability.

Another common question is:

> **What problem does Write Sharding solve?**

It prevents a single partition from becoming overloaded when many write requests target the same partition key.

Another common question is:

> **What is the downside of Write Sharding?**

Reads become more complex because the application must query multiple shards and merge the results. This is usually an acceptable trade-off for high-write workloads.

---

# Key Takeaways

- Write Sharding distributes writes across multiple partition keys to prevent hot partitions.
- Shard identifiers may be random, hash-based, or combined with time buckets.
- The pattern dramatically improves write scalability and throughput.
- Reads require querying multiple shards and aggregating results.
- Write Sharding is commonly used in IoT, logging, analytics, messaging, and financial systems.
- It is a foundational DynamoDB scaling technique for applications with extremely high write volumes.