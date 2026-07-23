# 12 - Adaptive Capacity

## Overview

One of the most common misconceptions about DynamoDB is that if a table has enough Read Capacity Units (RCUs) and Write Capacity Units (WCUs), it can never become a bottleneck.

In reality, **capacity is distributed across partitions**, not shared equally across the table as a single pool.

Consider a table with a total throughput of:

```text
20,000 RCUs

20,000 WCUs
```

At first glance, this appears to be more than enough.

However, if **90% of all requests target a single partition**, that partition may become overloaded while the remaining partitions remain mostly idle.

This problem is known as **partition imbalance**.

To reduce the impact of uneven traffic, DynamoDB introduces a feature called **Adaptive Capacity**.

Adaptive Capacity automatically shifts internal resources toward partitions experiencing higher demand, improving performance without requiring developers to manually rebalance data.

It is one of DynamoDB's most valuable optimization features, but it is also one of the most misunderstood.

---

# Why Adaptive Capacity Exists

Imagine an online shopping application.

Products are stored using:

```text
PK = ProductId
```

Most products receive only a few requests per hour.

```text
Product A

↓

10 Reads
```

```text
Product B

↓

8 Reads
```

```text
Product C

↓

12 Reads
```

Everything is balanced.

Now imagine a celebrity recommends one product on social media.

Suddenly:

```text
Product X

↓

250,000 Requests
```

while every other product continues receiving only a handful of requests.

The table still has plenty of unused capacity.

The problem is that **one partition receives almost all the traffic**.

---

# Capacity Distribution

Consider a table divided into four partitions.

```text
                DynamoDB Table

      +---------------------------------+

      |                                 |

      +---------------------------------+

          │      │      │      │

          ▼      ▼      ▼      ▼

      P1     P2     P3     P4
```

Traffic is evenly distributed.

```text
P1

200 Requests/sec

P2

220 Requests/sec

P3

180 Requests/sec

P4

210 Requests/sec
```

Everything performs efficiently.

Now traffic changes.

```text
P1

20 Requests/sec

P2

15 Requests/sec

P3

12 Requests/sec

P4

4,000 Requests/sec
```

Although the table still has significant unused capacity, Partition 4 becomes the bottleneck.

---

# Without Adaptive Capacity

Without adaptive capacity, every partition receives approximately the same internal resource allocation.

```text
Table Capacity

↓

25%

25%

25%

25%
```

If one partition exceeds its share, requests begin failing.

```text
Application

↓

Partition 4

↓

Throttling
```

Meanwhile:

```text
Partition 1

Mostly Idle
```

This is inefficient because unused resources exist elsewhere in the table.

---

# How Adaptive Capacity Works

Adaptive Capacity continuously monitors traffic patterns.

Conceptually:

```text
Read Requests

↓

Traffic Analysis

↓

Detect Hot Partition

↓

Allocate Additional Resources

↓

Reduce Throttling
```

Instead of keeping resources evenly divided, DynamoDB temporarily shifts additional internal throughput toward the busy partition.

Applications continue functioning without requiring infrastructure changes.

---

# Dynamic Resource Allocation

Suppose traffic suddenly becomes uneven.

Before:

```text
Partition A

25%

Partition B

25%

Partition C

25%

Partition D

25%
```

After Adaptive Capacity:

```text
Partition A

15%

Partition B

15%

Partition C

15%

Partition D

55%
```

Notice that the total table capacity has **not increased**.

Instead, DynamoDB reallocates existing internal resources to where they are needed most.

---

# What Adaptive Capacity Does NOT Do

A common misconception is that Adaptive Capacity creates unlimited throughput.

It does not.

It cannot:

- Create infinite capacity
- Eliminate every hot partition
- Fix poor schema design
- Replace good partition keys

If every request targets exactly the same partition key, Adaptive Capacity eventually reaches its limits.

Good data modeling is still essential.

---

# Adaptive Capacity vs Auto Scaling

These two concepts are often confused.

## Adaptive Capacity

Focuses on:

```text
Traffic Distribution

↓

Within Existing Capacity
```

It reallocates resources **inside** the table.

---

## Auto Scaling

Focuses on:

```text
Increase Total Capacity

↓

More RCUs

More WCUs
```

It increases the table's overall throughput.

Think of them as solving different problems.

| Feature | Adaptive Capacity | Auto Scaling |
|----------|-------------------|--------------|
| Increases Total Capacity | ❌ No | ✅ Yes |
| Redistributes Existing Capacity | ✅ Yes | ❌ No |
| Handles Temporary Hotspots | ✅ Yes | Limited |
| Requires Configuration | No | Yes |

---

# Adaptive Capacity and Partition Keys

Adaptive Capacity works best when partition keys already distribute data reasonably well.

Example:

```text
UserId

↓

Millions of Unique Users
```

Traffic occasionally spikes for one user.

Adaptive Capacity can often compensate.

Poor example:

```text
Country
```

Every request:

```text
USA
```

↓

Same Partition

Adaptive Capacity cannot indefinitely compensate for a fundamentally poor partition key.

---

# Real-World Example

Imagine an online ticket booking system.

Normally:

```text
Movie A

100 Requests/sec

Movie B

95 Requests/sec

Movie C

110 Requests/sec
```

A blockbuster movie releases.

```text
Movie X

↓

50,000 Requests/sec
```

Without Adaptive Capacity:

```text
Movie X

↓

Request Throttling
```

With Adaptive Capacity:

DynamoDB temporarily allocates additional resources to the busy partition, allowing significantly more requests to succeed while the surge lasts.

Once demand returns to normal, resources are redistributed again.

---

# Monitoring Adaptive Capacity

Adaptive Capacity operates automatically.

There is no API to enable or disable it.

Instead, engineers monitor the effects through CloudWatch metrics such as:

- ThrottledRequests
- ReadThrottleEvents
- WriteThrottleEvents
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits

If throttling continues despite Adaptive Capacity, the issue is usually one of:

- Poor partition key design
- Insufficient overall capacity
- Extremely skewed traffic

---

# Best Practices

- Design high-cardinality partition keys.
- Assume Adaptive Capacity is a safety net—not a design strategy.
- Monitor CloudWatch metrics for traffic imbalance.
- Load test applications using realistic traffic patterns.
- Combine Adaptive Capacity with Auto Scaling for production workloads.

---

# Common Mistakes

## Assuming Adaptive Capacity Eliminates Hot Partitions

It reduces the impact of temporary hotspots.

It does not eliminate them.

---

## Ignoring Data Modeling

Adaptive Capacity cannot compensate for a partition key that directs nearly all requests to the same partition.

Schema design remains the primary factor in scalability.

---

## Confusing It with Auto Scaling

Adaptive Capacity redistributes existing resources.

Auto Scaling increases the total resources available.

They solve different problems and often work together.

---

# Interview Notes

A common interview question is:

> **If DynamoDB already has Auto Scaling, why does it need Adaptive Capacity?**

Because they address different layers of the system.

Auto Scaling increases the **total throughput** of a table.

Adaptive Capacity redistributes that throughput among partitions when traffic becomes uneven.

For example, a table may have sufficient total RCUs, yet still experience throttling because one partition receives nearly all requests. Adaptive Capacity helps mitigate this imbalance, whereas Auto Scaling alone would simply increase the table's overall capacity.

---

# Key Takeaways

- Capacity in DynamoDB is consumed at the partition level, not as a single shared pool.
- Uneven traffic can overload one partition while others remain underutilized.
- Adaptive Capacity automatically reallocates internal resources toward busy partitions.
- It improves performance and reduces throttling caused by temporary traffic imbalance.
- Adaptive Capacity does **not** replace good partition key design.
- It works best alongside high-cardinality partition keys and appropriate capacity planning.
- Adaptive Capacity and Auto Scaling solve different problems and complement each other in production systems.