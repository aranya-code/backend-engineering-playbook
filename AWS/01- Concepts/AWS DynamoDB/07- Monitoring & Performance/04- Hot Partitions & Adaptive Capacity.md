# 04 - Hot Partitions & Adaptive Capacity

## Overview

One of the biggest misconceptions about DynamoDB is that simply increasing the table's Read Capacity Units (RCUs) or Write Capacity Units (WCUs) will solve every performance problem.

In reality, **DynamoDB distributes data across multiple physical partitions**, and **capacity is also distributed across those partitions**.

If a disproportionate amount of traffic targets a single partition, that partition can become overloaded even when the table has plenty of unused capacity overall.

This phenomenon is known as a **Hot Partition**.

To reduce the impact of uneven traffic, DynamoDB automatically uses **Adaptive Capacity**, which reallocates throughput to busy partitions whenever possible.

Understanding hot partitions is one of the most important topics for designing highly scalable DynamoDB applications.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What partitions are
- How DynamoDB distributes data
- What causes hot partitions
- How Adaptive Capacity works
- Partition throughput limits
- Detection strategies
- Prevention techniques
- Production design patterns
- Best practices
- Interview questions

---

# How DynamoDB Stores Data

DynamoDB tables are automatically divided into multiple **physical partitions**.

```text
                Orders Table

                     │

     ┌───────────────┼───────────────┐

     ▼               ▼               ▼

 Partition A    Partition B    Partition C
```

AWS manages these partitions automatically.

Applications never interact with partitions directly.

---

# How Items Are Assigned

DynamoDB hashes the **Partition Key**.

```text
CustomerID

↓

Hash Function

↓

Partition
```

Example:

```text
Customer-101

↓

Hash

↓

Partition A
```

```text
Customer-502

↓

Hash

↓

Partition C
```

Even distribution depends entirely on good partition key design.

---

# Normal Traffic Distribution

A healthy workload spreads requests across many partitions.

```text
           1000 Requests

               │

     ┌─────────┼─────────┐

     ▼         ▼         ▼

   330       335       335
```

Every partition shares the workload.

---

# Hot Partition

Suppose one product becomes extremely popular.

```text
           1000 Requests

               │

     ┌─────────┼─────────┐

     ▼         ▼         ▼

    970        15        15
```

Partition A receives almost all traffic.

Although the table has available capacity, Partition A becomes overloaded.

---

# Why Hot Partitions Occur

Common causes include:

- Poor partition key design
- Popular products
- Viral content
- Flash sales
- Sequential IDs
- Current timestamp as partition key
- Single-tenant workloads

---

# Example

Bad partition key:

```text
Country

↓

India
```

Millions of users:

```text
India

↓

Same Partition
```

This creates a hotspot.

---

Better design:

```text
CustomerID
```

or

```text
OrderID
```

Traffic becomes naturally distributed.

---

# Sequential Keys

Avoid sequential values.

Example:

```text
Order-1

Order-2

Order-3

Order-4
```

These often generate uneven partition utilization over time.

Prefer:

```text
UUID

ULID

Random IDs
```

or a well-designed composite key.

---

# Timestamp Hotspots

Bad example:

```text
Partition Key

↓

Current Date
```

Every new write targets today's partition.

Example:

```text
2026-08-01

↓

Millions of Writes
```

---

Better:

```text
CustomerID

+

Timestamp
```

or

```text
Shard Number

+

Timestamp
```

---

# Partition Throughput

Each partition has finite throughput.

```text
Partition

↓

Capacity Limit

↓

Throttling
```

Increasing total table capacity does not automatically remove a hotspot.

---

# Hot Partition Symptoms

Applications may experience:

- Read throttling
- Write throttling
- Increased latency
- Retry storms
- Timeout errors

Even though CloudWatch shows unused table capacity.

---

# Detecting Hot Partitions

Common indicators:

```text
ReadThrottleEvents

WriteThrottleEvents

SuccessfulRequestLatency
```

Symptoms include:

- Low overall utilization
- High throttling
- Uneven traffic distribution

---

# Adaptive Capacity

Adaptive Capacity helps DynamoDB automatically redistribute throughput.

```text
Normal Capacity

↓

Busy Partition

↓

Adaptive Capacity

↓

More Throughput
```

This reduces throttling without manual intervention.

---

# Adaptive Capacity Architecture

```text
              DynamoDB

                  │

        Monitor Partition Usage

                  │

                  ▼

      Detect Uneven Traffic

                  │

                  ▼

      Reallocate Capacity

                  │

                  ▼

      Reduce Throttling
```

Applications do not need to enable this feature.

It is built into DynamoDB.

---

# What Adaptive Capacity Does

Adaptive Capacity can:

- Increase throughput for busy partitions
- Reduce throttling
- Improve application performance
- Automatically respond to traffic changes

It works without changing your application code.

---

# What Adaptive Capacity Cannot Fix

Adaptive Capacity is **not** a replacement for good data modeling.

It cannot fully compensate for:

- One partition receiving nearly all traffic
- Extremely poor partition key selection
- Constant write concentration on a single key

Good schema design remains the primary solution.

---

# Write Sharding

A common solution for write hotspots is **write sharding**.

Instead of:

```text
OrderQueue
```

Use:

```text
OrderQueue#1

OrderQueue#2

OrderQueue#3

OrderQueue#4
```

Writes are distributed across multiple partition keys.

---

# Random Suffix Strategy

Example:

Instead of:

```text
Customer123
```

Use:

```text
Customer123#1

Customer123#2

Customer123#3
```

Requests become evenly distributed.

Applications merge the results during reads if necessary.

---

# Composite Partition Keys

Good example:

```text
TenantID

+

CustomerID
```

Instead of:

```text
TenantID
```

Composite keys improve traffic distribution.

---

# Production Example

E-commerce flash sale:

Bad design:

```text
Partition Key

↓

ProductID
```

One viral product receives millions of requests.

Better:

```text
ProductID

+

Shard Number
```

Traffic spreads across multiple partitions.

---

# CloudWatch Monitoring

Monitor:

```text
ReadThrottleEvents

WriteThrottleEvents

ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

SuccessfulRequestLatency
```

Combine metrics with application logs to identify hotspots.

---

# Production Architecture

```text
                Application

                      │

                      ▼

               DynamoDB Table

                      │

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

   Partition A   Partition B   Partition C

        ▲

        │

 Adaptive Capacity

        │

 Reallocate Throughput
```

---

# Best Practices

- Choose high-cardinality partition keys.
- Avoid sequential partition keys.
- Avoid current timestamps as the only partition key.
- Use composite keys where appropriate.
- Use write sharding for write-heavy workloads.
- Monitor throttling continuously.
- Load test before production deployments.

---

# Common Mistakes

## Assuming More RCUs Solve Everything

Increasing RCUs helps only if capacity is evenly distributed.

Hot partitions may continue throttling.

---

## Using Low-Cardinality Keys

Poor:

```text
Country
```

Better:

```text
CustomerID
```

---

## Ignoring Traffic Patterns

A schema that works during testing may fail under production traffic.

Design based on expected access patterns, not sample data.

---

## Depending Entirely on Adaptive Capacity

Adaptive Capacity improves resilience but is not a substitute for proper partition key design.

---

# Production Considerations

Large-scale systems often implement:

- Composite partition keys
- Write sharding
- Randomized suffixes
- Traffic analysis
- Load testing
- CloudWatch dashboards
- Continuous monitoring

These techniques help maintain low latency and high throughput under heavy workloads.

---

# Interview Notes

A common interview question is:

> **What is a hot partition in DynamoDB?**

A hot partition occurs when a disproportionate amount of read or write traffic is directed to a single physical partition, causing throttling even though the table may have sufficient overall capacity.

---

Another common question is:

> **What is Adaptive Capacity?**

Adaptive Capacity is a built-in DynamoDB feature that automatically reallocates throughput to heavily used partitions, helping reduce throttling caused by uneven traffic distribution.

---

Another common question is:

> **Can Adaptive Capacity eliminate all hot partition problems?**

No. It helps mitigate uneven workloads, but it cannot fully compensate for poor partition key design or workloads that consistently target a single partition key.

---

Another common question is:

> **How do you prevent hot partitions?**

Use high-cardinality partition keys, composite keys, write sharding, randomized suffixes where appropriate, and design the schema around actual access patterns. Monitor CloudWatch metrics and validate the design with load testing.

---

# Key Takeaways

- DynamoDB automatically distributes data across physical partitions.
- Poor partition key design can create hot partitions that cause throttling and increased latency.
- Adaptive Capacity automatically reallocates throughput to busy partitions but does not replace good schema design.
- High-cardinality partition keys, composite keys, and write sharding are common techniques for preventing hotspots.
- Monitor CloudWatch metrics such as throttling events and latency to detect partition-related issues.
- Designing for even traffic distribution is essential for building highly scalable DynamoDB applications.