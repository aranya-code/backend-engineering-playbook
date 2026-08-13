# 10 - Time-Series Data Modeling

## Overview

Many modern applications continuously generate data over time.

Examples include:

- IoT sensor readings
- Application logs
- Financial transactions
- User activity
- GPS locations
- Monitoring metrics
- Audit logs
- Clickstream events

This type of data is called **time-series data**.

Unlike relational databases, DynamoDB is particularly well-suited for time-series workloads because its **sorted sort keys**, **horizontal scalability**, and **high write throughput** naturally support chronological data.

However, poor modeling can quickly create **hot partitions**, making time-series data one of the most important DynamoDB design topics.

---

# What is Time-Series Data?

Time-series data consists of records ordered by time.

Example:

```text
Temperature Sensor

↓

10:00 AM

↓

10:01 AM

↓

10:02 AM

↓

10:03 AM
```

Each event has:

- Entity
- Timestamp
- Value

Example:

```text
Device

Timestamp

Temperature
```

---

# Common Use Cases

Time-series workloads are everywhere.

Examples:

```text
IoT

↓

Sensor Readings
```

```text
Cloud Monitoring

↓

CPU Metrics
```

```text
Security

↓

Audit Logs
```

```text
Banking

↓

Transactions
```

```text
Fitness

↓

Heart Rate
```

```text
Ride Sharing

↓

GPS Coordinates
```

---

# SQL Approach

Relational databases typically store:

```text
Readings

ID

DeviceID

Timestamp

Value
```

Query:

```sql
SELECT *

FROM Readings

WHERE DeviceID = 100

ORDER BY Timestamp DESC

LIMIT 100;
```

As data grows into billions of rows, maintaining indexes and partitions becomes increasingly complex.

---

# DynamoDB Approach

Use:

- Partition Key → Entity
- Sort Key → Timestamp

Example:

```text
PK = DEVICE#100

SK = 2026-07-23T10:00:00Z
```

Another reading:

```text
PK = DEVICE#100

SK = 2026-07-23T10:01:00Z
```

Another:

```text
PK = DEVICE#100

SK = 2026-07-23T10:02:00Z
```

Everything is automatically ordered.

---

# Visual Representation

```text
DEVICE#100

│

├── 2026-07-23T10:00

├── 2026-07-23T10:01

├── 2026-07-23T10:02

├── 2026-07-23T10:03

└── 2026-07-23T10:04
```

The sort key naturally represents time.

---

# Retrieving Recent Data

Suppose an application needs:

> Show the latest 20 sensor readings.

Query:

```text
PK = DEVICE#100

↓

Reverse Order

↓

Limit 20
```

No sorting is required.

DynamoDB returns items in sort key order.

---

# Time Range Queries

Retrieve readings between:

```text
10:00

↓

10:30
```

Query:

```text
PK = DEVICE#100

SK BETWEEN

2026-07-23T10:00

AND

2026-07-23T10:30
```

Efficient.

No scan required.

---

# ISO-8601 Timestamps

A common best practice is using ISO-8601 timestamps.

Example:

```text
2026-07-23T09:15:00Z

2026-07-23T10:00:00Z

2026-07-23T10:30:45Z
```

Why?

Because lexicographical ordering matches chronological ordering.

This makes prefix and range queries work naturally.

---

# Example – Application Logs

Partition:

```text
SERVICE#Payment
```

Sort keys:

```text
2026-07-23T10:00

2026-07-23T10:01

2026-07-23T10:02
```

Query:

```text
Latest Logs
```

Or:

```text
Logs Between

10:00

and

11:00
```

---

# Example – Banking

Account:

```text
ACCOUNT#500
```

Transactions:

```text
2026-07-21T08:00

2026-07-22T10:30

2026-07-23T15:00
```

Application:

```text
Last 30 Transactions
```

One Query.

---

# Example – IoT

Device:

```text
DEVICE#500
```

Sensor readings:

```text
08:00

08:01

08:02

08:03
```

Dashboard:

```text
Latest Reading
```

Or:

```text
Last Hour
```

Both use the same partition.

---

# Hot Partition Problem

Suppose:

One device generates:

```text
50,000 Writes

Per Second
```

Partition:

```text
DEVICE#100
```

Every write targets:

```text
One Partition
```

Result:

```text
Hot Partition
```

Performance suffers.

---

# Time Bucketing

Instead of:

```text
DEVICE#100
```

Use:

```text
DEVICE#100#2026-07
```

Or:

```text
DEVICE#100#2026-07-23
```

Example:

```text
PK = DEVICE#100#2026-07-23

SK = 10:01
```

Tomorrow:

```text
PK = DEVICE#100#2026-07-24
```

Load becomes distributed over multiple partitions.

---

# Bucket Granularity

Choose bucket size based on write volume.

Low traffic:

```text
Daily Bucket
```

Medium traffic:

```text
Hourly Bucket
```

High traffic:

```text
Minute Bucket
```

Very high traffic:

```text
Hash Sharding

+

Time Bucket
```

---

# Combining Time Buckets with Sharding

Instead of:

```text
DEVICE#100
```

Use:

```text
DEVICE#100#Shard1#2026-07-23
```

```text
DEVICE#100#Shard2#2026-07-23
```

Writes become evenly distributed.

Reads aggregate results across shards when necessary.

---

# Using TTL

Many time-series datasets expire naturally.

Examples:

- Session logs
- Temporary metrics
- Cache entries
- Monitoring events

Add:

```text
TTL

↓

Expiration Timestamp
```

Expired items are automatically removed by DynamoDB.

---

# Archiving Old Data

Many organizations retain historical data.

Workflow:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

Amazon S3

↓

Athena / Glacier
```

Recent data stays in DynamoDB.

Historical data moves to cheaper storage.

---

# Global Secondary Index Example

Suppose logs are stored by service.

Need:

```text
Find Logs

By Severity
```

Create GSI:

```text
PK = ERROR

SK = Timestamp
```

Now:

```text
Query

ERROR

↓

Latest Errors
```

without scanning the main table.

---

# Performance Considerations

Time-series workloads often have:

- High write throughput
- Sequential timestamps
- Frequent recent-data queries

Design considerations:

- Even partition distribution
- Appropriate bucket sizing
- Efficient range queries
- Automatic data expiration

---

# Best Practices

- Use ISO-8601 timestamps for sort keys.
- Query using ranges instead of scans.
- Bucket data to avoid hot partitions.
- Archive historical records.
- Use TTL for temporary datasets.
- Monitor write throughput and partition utilization.

---

# Common Mistakes

## One Partition Forever

Avoid:

```text
PK = DEVICE#100
```

for years of high-volume data.

Partition sizes and write traffic will grow continuously.

---

## Scanning for Date Ranges

Never:

```text
Scan

↓

Filter Timestamp
```

Always use:

```text
Query

SK BETWEEN
```

---

## Poor Timestamp Format

Avoid:

```text
July 23

10 AM
```

Use:

```text
2026-07-23T10:00:00Z
```

to preserve lexical ordering.

---

## Ignoring Data Retention

Time-series datasets grow indefinitely.

Implement TTL or archival strategies early.

---

# Real-World Example

A cloud monitoring platform stores CPU metrics for thousands of virtual machines.

Partition key:

```text
VM#123#2026-07-23
```

Sort key:

```text
2026-07-23T14:35:12Z
```

Engineers can retrieve:

- Latest metrics
- Metrics for a specific time window
- Daily performance history

while older records are automatically archived to Amazon S3 for long-term analytics.

---

# Architecture Perspective

```text
Application

        │

        ▼

Query

PK = DEVICE#100#2026-07-23

        │

        ▼

Partition

DEVICE#100#2026-07-23

        │

        ├── 10:00

        ├── 10:01

        ├── 10:02

        ├── 10:03

        └── 10:04

        │

        ▼

Recent Sensor Data
```

The partition represents a bounded time window, while the sort key maintains chronological order.

---

# Interview Notes

A common interview question is:

> **How do you model time-series data in DynamoDB?**

Typically, the entity identifier is used as the partition key and an ISO-8601 timestamp is used as the sort key. For high-volume workloads, time bucketing (daily, hourly, etc.) is added to the partition key to prevent hot partitions.

Another common question is:

> **Why use ISO-8601 timestamps instead of Unix timestamps?**

Both work, but ISO-8601 timestamps are human-readable and maintain chronological order when sorted lexicographically, making debugging and range queries easier. Unix timestamps are more compact and may be preferred in storage-constrained or performance-sensitive scenarios.

Another common question is:

> **How do you prevent hot partitions in time-series workloads?**

Use time bucketing, write sharding, or a combination of both. This distributes writes across multiple partitions instead of concentrating all traffic on a single partition key.

---

# Key Takeaways

- Time-series data consists of records ordered by time.
- Model time-series data using an entity-based partition key and a timestamp sort key.
- Use ISO-8601 timestamps to support efficient range queries and natural ordering.
- Prevent hot partitions with time bucketing and write sharding.
- Use TTL for automatic expiration and archive historical data to Amazon S3 when appropriate.
- Proper time-series modeling enables DynamoDB to handle massive write throughput while maintaining low-latency queries.