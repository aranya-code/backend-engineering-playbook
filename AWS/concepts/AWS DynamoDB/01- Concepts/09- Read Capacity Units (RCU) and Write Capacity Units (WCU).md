# 09 - Read Capacity Units (RCU) and Write Capacity Units (WCU)

## Overview

One of the biggest misconceptions about DynamoDB is that storage is the primary resource being billed.

It is not.

Unlike traditional databases where storage size often determines cost, DynamoDB is fundamentally designed around **throughput**. The service assumes that the most valuable resource is not disk space, but the ability to process reads and writes with predictable low latency.

This is why DynamoDB introduces the concept of **Capacity Units**.

Every request consumes capacity.

Whether an application reads a single customer record or writes millions of IoT events, DynamoDB measures the workload using Read Capacity Units (RCUs) and Write Capacity Units (WCUs).

Understanding these units is essential for:

- Performance tuning
- Capacity planning
- Cost optimization
- Avoiding throttling
- Designing scalable applications

---

# Why Capacity Units Exist

Imagine AWS simply allowed unlimited reads and writes without restrictions.

Suppose two customers share the same underlying infrastructure.

Customer A

```text
100 Requests / Second
```

Customer B

```text
2 Million Requests / Second
```

Without resource allocation, Customer B could monopolize the underlying hardware, degrading performance for everyone else.

Capacity Units solve this problem.

Instead of thinking in terms of servers or CPUs, DynamoDB measures how much work each request performs.

This abstraction allows AWS to:

- Allocate resources fairly
- Guarantee predictable performance
- Scale automatically
- Prevent noisy-neighbor problems

---

# Throughput vs Storage

Traditional databases often emphasize storage.

```text
Database

↓

500 GB Storage

↓

Enough Capacity
```

DynamoDB separates these concerns.

Storage determines **how much data** you can keep.

Capacity determines **how quickly** you can access it.

Example:

Database A

```text
5 TB

Very Few Reads
```

Database B

```text
10 GB

100,000 Reads/Second
```

Although Database A stores far more information, Database B requires significantly more processing power.

Capacity pricing reflects this reality.

---

# Read Capacity Units (RCUs)

An RCU represents the amount of throughput required to perform read operations.

Under normal circumstances:

```text
1 RCU

=

1 Strongly Consistent Read

Up to 4 KB
```

If the item is larger than 4 KB, additional RCUs are consumed.

---

# Example

Item Size

```text
3 KB
```

Consumes

```text
1 RCU
```

Item Size

```text
7 KB
```

Consumes

```text
2 RCUs
```

Because:

```text
4 KB

+

4 KB

=

8 KB Capacity
```

Even though only 7 KB was read, DynamoDB rounds up to the next 4 KB boundary.

---

# Eventually Consistent Reads

Eventually consistent reads require fewer resources.

```text
1 RCU

↓

2 Eventually Consistent Reads

Up to 4 KB Each
```

This means eventually consistent reads are approximately **50% cheaper** than strongly consistent reads.

Example:

```text
1000 Eventually Consistent Reads
```

consume roughly the same capacity as

```text
500 Strongly Consistent Reads
```

For workloads that can tolerate slightly stale data, eventual consistency significantly reduces cost.

---

# Strongly Consistent Reads

Strong consistency guarantees that the latest successful write is returned.

Because the database must coordinate more carefully with storage replicas, these reads consume more capacity.

```text
1 Strong Read

↓

1 RCU
```

Strong consistency should only be used when applications genuinely require the latest committed value.

Examples include:

- Banking
- Inventory
- Payment systems

---

# Write Capacity Units (WCUs)

A WCU represents the throughput required to write data.

Under normal circumstances:

```text
1 WCU

=

1 Write

Up to 1 KB
```

Unlike reads, write capacity is calculated using **1 KB** increments.

---

# Example

Item Size

```text
800 Bytes
```

Consumes

```text
1 WCU
```

Item Size

```text
2.3 KB
```

Consumes

```text
3 WCUs
```

Because DynamoDB rounds upward.

---

# Why Writes Cost More

Writing data is significantly more expensive than reading it.

A write operation involves much more than storing bytes.

Internally, DynamoDB must:

- Validate the request
- Locate the correct partition
- Persist the data
- Update indexes
- Replicate the write
- Ensure durability
- Acknowledge success

Each write therefore consumes more system resources.

---

# Capacity Calculation Examples

## Example 1

Item

```text
2 KB
```

Read

```text
Strong Consistency
```

Capacity

```text
1 RCU
```

---

## Example 2

Item

```text
6 KB
```

Read

```text
Strong Consistency
```

Capacity

```text
2 RCUs
```

---

## Example 3

Item

```text
6 KB
```

Eventually Consistent

Capacity

```text
1 RCU
```

---

## Example 4

Item

```text
3 KB
```

Write

Capacity

```text
3 WCUs
```

---

# Item Size Directly Impacts Cost

Every attribute contributes to item size.

Consider:

```json
{
    "UserId":"1001",
    "Name":"Alice"
}
```

versus

```json
{
    "UserId":"1001",
    "Name":"Alice",
    "Address":"Very Long Address...",
    "Biography":"Several KB...",
    "Preferences":{...}
}
```

The second item consumes:

- More storage
- More network bandwidth
- More RCUs
- More WCUs

Large items therefore increase both performance cost and monetary cost.

Keeping items compact is one of the most effective optimization strategies in DynamoDB.

---

# Secondary Indexes Also Consume Capacity

Many developers assume indexes are "free."

They are not.

Whenever an item is written:

```text
Write

↓

Base Table

↓

Global Secondary Index

↓

Local Secondary Index
```

Each index must also be updated.

Consequently:

- Additional WCUs are consumed.
- Storage increases.
- Write latency may increase slightly.

Indexes improve query flexibility but are not without cost.

---

# Transactions Consume More Capacity

Transactional operations require additional coordination.

As a result:

- Transactional reads consume twice the normal read capacity.
- Transactional writes consume twice the normal write capacity.

This trade-off provides ACID guarantees while preserving DynamoDB's distributed architecture.

---

# Capacity and Hot Partitions

Capacity is allocated across partitions.

Suppose a table has enough total capacity.

```text
1000 RCUs
```

If nearly every request targets one partition:

```text
Partition A

980 RCUs

Partition B

10 RCUs

Partition C

10 RCUs
```

The application may still experience throttling.

This demonstrates why choosing a good partition key is just as important as provisioning sufficient capacity.

---

# Monitoring Capacity

CloudWatch provides metrics including:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ThrottledRequests
- SuccessfulRequestLatency

Monitoring these metrics helps identify:

- Traffic spikes
- Hot partitions
- Under-provisioning
- Inefficient access patterns

Capacity planning should always be based on real production metrics rather than estimates.

---

# Best Practices

- Keep items as small as practical.
- Use eventually consistent reads whenever possible.
- Avoid unnecessary indexes.
- Design efficient partition keys.
- Monitor consumed capacity continuously.
- Optimize access patterns before increasing capacity.

---

# Common Mistakes

- Assuming storage determines cost.
- Ignoring item size.
- Using strong consistency everywhere.
- Overusing transactional operations.
- Creating unnecessary secondary indexes.
- Increasing capacity instead of fixing poor schema design.

---

# Interview Notes

One of the most common interview questions is:

> **Why does DynamoDB measure capacity using 4 KB reads and 1 KB writes instead of charging per request?**

Because the amount of work performed by the database depends on the size of the data being processed.

Reading a 500-byte item requires significantly fewer resources than reading a 40 KB document.

Capacity Units provide a predictable way to measure actual workload rather than simply counting API calls.

This model also encourages efficient schema design, compact items, and optimized access patterns.

---

# Key Takeaways

- Capacity Units measure throughput rather than storage.
- Reads are calculated in 4 KB increments.
- Writes are calculated in 1 KB increments.
- Item size directly impacts cost and performance.
- Eventually consistent reads consume half the capacity of strongly consistent reads.
- Secondary indexes and transactions increase capacity consumption.
- Good schema design is often a better optimization than simply provisioning more capacity.