# 13 - Hot Partitions

## Overview

One of the biggest reasons DynamoDB applications experience throttling is **not because the table lacks capacity**, but because **one partition receives a disproportionate amount of traffic**.

This phenomenon is known as a **Hot Partition**.

Hot partitions are among the most common production issues encountered when designing DynamoDB applications. They are also one of the easiest mistakes to make because a table can appear healthy overall while a single partition is overloaded.

Understanding hot partitions is critical for designing scalable systems because **DynamoDB scales horizontally only when traffic is evenly distributed**.

---

# What is a Hot Partition?

A hot partition occurs when one physical partition receives significantly more read or write requests than the others.

Imagine a DynamoDB table with four partitions.

```text
                 DynamoDB Table

        +-----------------------------+

        |                             |

        +-----------------------------+

            │      │      │      │

            ▼      ▼      ▼      ▼

        P1      P2      P3      P4
```

Normally, traffic is evenly distributed.

```text
P1

250 Requests/sec

P2

230 Requests/sec

P3

260 Requests/sec

P4

240 Requests/sec
```

Everything operates efficiently.

Now imagine one partition suddenly receives nearly all requests.

```text
P1

15 Requests/sec

P2

20 Requests/sec

P3

18 Requests/sec

P4

15,000 Requests/sec
```

Partition 4 becomes overloaded.

This is a **Hot Partition**.

---

# Why Hot Partitions Occur

Hot partitions are almost always caused by **poor partition key selection**.

Remember:

```text
Partition Key

↓

Hash Function

↓

Physical Partition
```

If many requests use the same partition key, they all resolve to the same physical partition.

Example

```text
PK = USER#1001
```

Every request

```text
↓

Partition A
```

No matter how much unused capacity exists elsewhere, every operation must wait for Partition A.

---

# Example 1 — Celebrity Effect

Imagine a social media platform.

Posts are stored using:

```text
PK = UserId
```

Normally:

```text
User A

100 Requests

User B

120 Requests

User C

95 Requests
```

One celebrity publishes a new post.

```text
Celebrity User

↓

3 Million Requests
```

Every request targets the same partition.

Result:

```text
Hot Partition
```

---

# Example 2 — Flash Sale

Suppose an e-commerce application stores inventory.

```text
PK = ProductId
```

Most products receive modest traffic.

```text
Product A

50 Reads/sec

Product B

60 Reads/sec

Product C

40 Reads/sec
```

A flash sale begins.

```text
PlayStation 6

↓

250,000 Reads/sec
```

One partition suddenly receives nearly all traffic.

The application experiences throttling despite having plenty of unused table capacity.

---

# Example 3 — Poor Key Design

Suppose an engineer chooses:

```text
Partition Key

Country
```

The data looks like:

```text
USA

Canada

UK

Germany
```

Most customers live in:

```text
USA
```

Traffic becomes:

```text
USA

↓

Millions of Requests

Canada

↓

Thousands

UK

↓

Thousands
```

One partition handles nearly the entire workload.

---

# Why Table Capacity Doesn't Solve the Problem

Consider a table with:

```text
100,000 RCUs
```

Traffic

```text
Partition A

95,000 RCUs

Partition B

2,000 RCUs

Partition C

1,500 RCUs

Partition D

1,500 RCUs
```

The table still has unused capacity.

Yet:

```text
Partition A

↓

Throttling
```

The bottleneck is **distribution**, not total throughput.

Adding more RCUs to the table often fails to solve the problem because requests continue targeting the same partition.

---

# Symptoms of a Hot Partition

Applications typically experience:

- Increased latency
- Read throttling
- Write throttling
- Intermittent request failures
- High retry counts
- Uneven CloudWatch metrics

Often, engineers mistakenly assume DynamoDB is under-provisioned.

The real issue is usually uneven request distribution.

---

# Detecting Hot Partitions

DynamoDB does not expose physical partitions directly.

Instead, engineers infer hot partitions using CloudWatch.

Useful metrics include:

- ReadThrottleEvents
- WriteThrottleEvents
- ThrottledRequests
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- SuccessfulRequestLatency

A sudden increase in throttling while total table capacity remains low is often a strong indicator of a hot partition.

---

# Adaptive Capacity Helps—but Doesn't Eliminate the Problem

As discussed in the previous chapter, DynamoDB includes **Adaptive Capacity**.

```text
Traffic Spike

↓

Adaptive Capacity

↓

Additional Internal Resources
```

Adaptive Capacity can reduce throttling caused by temporary traffic imbalance.

However:

It cannot create unlimited throughput.

If millions of requests continuously target a single partition key, Adaptive Capacity eventually reaches its limits.

Good schema design remains the primary solution.

---

# Designing Better Partition Keys

The best way to avoid hot partitions is to choose partition keys with **high cardinality**.

Good examples:

```text
UserId

OrderId

DeviceId

InvoiceId
```

Poor examples:

```text
Country

Department

Status

Gender

Category
```

High-cardinality keys naturally distribute requests across many partitions.

---

# Write Hot Partitions

Hot partitions are not limited to reads.

Consider an IoT application.

Every sensor writes using:

```text
PK = FactoryId
```

Thousands of sensors belong to the same factory.

```text
Factory A

↓

500,000 Writes/sec
```

Every write targets the same partition.

Result:

```text
Write Throttling
```

---

# Read Hot Partitions

Read hotspots are more common.

Examples include:

- Viral videos
- Trending products
- Popular social media accounts
- Breaking news
- Live sporting events

Although the underlying data rarely changes, millions of users request it simultaneously.

---

# Common Mitigation Strategies

## 1. Better Partition Keys

Instead of:

```text
Country
```

Use:

```text
UserId
```

---

## 2. Write Sharding

Suppose one customer generates enormous traffic.

Instead of:

```text
PK = CUSTOMER#1001
```

Use:

```text
CUSTOMER#1001#1

CUSTOMER#1001#2

CUSTOMER#1001#3

CUSTOMER#1001#4
```

Writes are distributed across multiple partitions.

The application later queries all shards and combines the results.

---

## 3. Random Suffixes

Example

Instead of:

```text
ORDER#1001
```

Use:

```text
ORDER#1001#A

ORDER#1001#B

ORDER#1001#C
```

Random suffixes distribute traffic more evenly.

This technique is useful for very high write workloads.

---

## 4. Calculated Suffixes

Instead of random values, applications can calculate the shard.

Example

```text
UserId % 10
```

Result

```text
USER#1001#7
```

Advantages:

- Predictable routing
- Easier reads
- Even distribution

---

## 5. DynamoDB Accelerator (DAX)

For read-heavy workloads:

```text
Application

↓

DAX Cache

↓

DynamoDB
```

Frequently requested items are served from memory rather than repeatedly hitting the same partition.

This dramatically reduces read hotspots.

---

# Real-World Example

Amazon's "Deal of the Day" begins.

One product receives:

```text
2 Million Reads

↓

Same ProductId

↓

Same Partition
```

Without mitigation:

```text
Throttling
```

Possible solutions:

- DAX
- Better partition key
- Read caching
- Request sharding
- Adaptive Capacity

Production systems often combine several of these techniques.

---

# Best Practices

- Design partition keys with high cardinality.
- Avoid partition keys based on low-cardinality business attributes.
- Monitor CloudWatch for throttling trends.
- Load test applications before production launches.
- Use DAX or application caching for extremely popular data.
- Consider write sharding for sustained high-write workloads.
- Review access patterns regularly as applications evolve.

---

# Common Mistakes

## Assuming More RCUs Solve Everything

Increasing capacity cannot fix poor request distribution.

---

## Ignoring Traffic Patterns

A schema that performs well during development may fail under real production traffic.

---

## Choosing Human-Friendly Keys

Business attributes such as:

```text
Country

Department

Status
```

often produce highly uneven request distribution.

---

## Believing Adaptive Capacity Removes All Bottlenecks

Adaptive Capacity helps absorb temporary hotspots.

It does not eliminate the need for good schema design.

---

# Interview Notes

A common interview question is:

> **Your DynamoDB table has 100,000 RCUs, but requests are still being throttled. Why?**

One possible explanation is a hot partition.

Although the table has sufficient total capacity, a single partition key may be receiving most of the requests. Since throughput is enforced at the partition level, that partition becomes saturated while other partitions remain mostly idle.

Another common question is:

> **How would you fix a hot partition?**

A senior engineer would evaluate the workload and choose one or more of the following:

- Redesign the partition key
- Introduce write sharding
- Add calculated or random suffixes
- Cache hot data using DAX
- Use application-side caching
- Verify that Adaptive Capacity is helping
- Reassess access patterns

The correct solution depends on whether the hotspot is read-heavy, write-heavy, temporary, or permanent.

---

# Key Takeaways

- A hot partition occurs when one physical partition receives a disproportionate amount of traffic.
- The root cause is usually poor partition key design rather than insufficient table capacity.
- Adding RCUs or WCUs does not necessarily resolve partition imbalance.
- Adaptive Capacity mitigates temporary hotspots but cannot compensate for fundamentally poor schemas.
- High-cardinality partition keys are the most effective long-term solution.
- Read sharding, write sharding, DAX, and caching are common techniques for handling high-traffic workloads.
- Monitoring CloudWatch metrics is essential for identifying and resolving hot partition issues before they impact production.