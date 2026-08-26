# 08 - Read Consistency Models

## Overview

One of the defining characteristics of distributed databases is that **data is replicated across multiple storage nodes**.

Replication improves:

- High Availability
- Fault Tolerance
- Read Scalability
- Disaster Recovery

However, replication introduces a fundamental challenge:

> **What happens if a client reads data before every replica has received the latest update?**

This is known as the **consistency problem**.

Unlike a single-server database, a distributed database cannot always guarantee that every server has exactly the same data at every instant.

DynamoDB addresses this challenge by allowing applications to choose between different **read consistency models**.

Understanding these models is essential because they directly impact:

- Application correctness
- Latency
- Throughput
- Cost
- User experience

---

# Why Consistency is a Problem

Imagine an item stored in DynamoDB.

```text
User Balance

$500
```

This item is replicated to multiple storage nodes.

```text
             Replica A

                $500

                  │

                  │

Replica B ---------------- Replica C

     $500              $500
```

Now suppose the application updates the balance.

```text
$500

↓

$650
```

The write reaches Replica A immediately.

```text
Replica A

$650
```

However...

Replica B and Replica C may still contain:

```text
$500
```

for a very short period.

If another application immediately performs a read, which value should be returned?

This is the core challenge of distributed databases.

---

# Replication Takes Time

Replication is extremely fast.

Usually measured in:

```text
Milliseconds
```

But **milliseconds are not zero**.

Even a tiny delay creates the possibility that different replicas temporarily contain different versions of the same item.

```text
Write

↓

Replica A Updated

↓

Replica B Updating

↓

Replica C Updating
```

This short window is called the **Replication Delay**.

---

# Consistency Models

DynamoDB supports two consistency models.

```text
Read Consistency

│

├── Eventually Consistent

└── Strongly Consistent
```

Each model makes a different trade-off between:

- Performance
- Cost
- Freshness

---

# Eventually Consistent Reads

Eventually Consistent Reads are the default behavior.

When an application performs a read:

```text
Application

↓

Read Request

↓

Nearest Replica

↓

Return Value
```

DynamoDB returns the value available at that replica.

Most of the time this is the newest value.

Occasionally, immediately after a write, it may still be the previous version.

Example:

```text
10:00:00

Balance = $500
```

Application performs update.

```text
10:00:01

Balance = $650
```

Another client immediately performs a read.

Replica not yet updated.

Result:

```text
$500
```

A few milliseconds later:

```text
$650
```

Eventually every replica converges to the same value.

Hence the name:

> **Eventually Consistent**

---

# Characteristics of Eventually Consistent Reads

Advantages

- Lower latency
- Higher throughput
- Lower cost
- Better scalability

Disadvantages

- May briefly return stale data

---

# Strongly Consistent Reads

Strongly Consistent Reads guarantee that the latest successful write is always returned.

```text
Application

↓

Read

↓

Latest Committed Value

↓

Return
```

If a write succeeds...

```text
Balance = $650
```

every subsequent strongly consistent read returns:

```text
$650
```

No stale data is returned.

---

# How Strong Consistency Works

Internally, DynamoDB ensures that the read is served only after the latest committed version is available.

Conceptually:

```text
Write

↓

Replication Coordination

↓

Read

↓

Latest Value
```

This additional coordination requires more work.

As a result:

- Higher latency
- More resource usage
- Higher RCU consumption

This is why:

```text
Strong Reads

↓

1 RCU

Eventually Consistent Reads

↓

2 Reads / RCU
```

---

# Strong Consistency is Not Faster

Many beginners assume:

```text
Strong Consistency

↓

Better Performance
```

The opposite is generally true.

Strong consistency requires additional coordination.

This increases:

- Processing
- Network communication
- Replica synchronization

Eventually consistent reads are usually faster.

---

# Timeline Example

Imagine a write occurs.

```text
10:00:00

User Name = Alice
```

Application updates:

```text
Alice

↓

Alicia
```

Timeline

```text
10:00:01

Write Completed
```

Replica A

```text
Alicia
```

Replica B

```text
Alice
```

Replica C

```text
Alice
```

Immediately afterward...

Eventually Consistent Read

may return

```text
Alice
```

Strongly Consistent Read

returns

```text
Alicia
```

A few milliseconds later...

All replicas contain:

```text
Alicia
```

---

# Which Operations Support Strong Consistency?

Strong consistency is supported only for:

- Base Tables
- Local Secondary Indexes (LSIs)

It is **not supported** for:

- Global Secondary Indexes (GSIs)
- Global Tables

Those services always provide eventually consistent reads because they span multiple partitions or Regions where synchronous coordination would significantly impact scalability and availability.

---

# Read-After-Write Consistency

Consider a common scenario.

```text
Create User

↓

Immediately Read User
```

With a strongly consistent read:

```text
Always Returns User
```

With an eventually consistent read:

```text
Usually Returns User

Occasionally Delayed
```

Applications that immediately read data after writing it should carefully choose the appropriate consistency model.

---

# Choosing the Right Consistency Model

## Banking

```text
Transfer Money

↓

Read Updated Balance
```

Requirements:

- No stale data
- Financial accuracy

Recommendation:

```text
Strongly Consistent Reads
```

---

## Shopping Cart

A customer adds an item.

Another request immediately loads the cart.

Strong consistency often provides a better user experience.

---

## Social Media Feed

Suppose a friend posts:

```text
Hello World
```

Another user sees it:

```text
100 milliseconds later
```

This delay is generally acceptable.

Recommendation:

```text
Eventually Consistent Reads
```

---

## Product Catalog

Product descriptions rarely change.

A brief delay before updates appear is acceptable.

Recommendation:

```text
Eventually Consistent Reads
```

---

# Consistency and CAP Theorem

Earlier we discussed the CAP Theorem.

```text
Consistency

Availability

Partition Tolerance
```

Because DynamoDB is a distributed database operating across multiple nodes, it must tolerate network partitions.

During temporary communication delays, AWS generally prioritizes:

- High Availability
- Partition Tolerance

Eventually consistent reads align with this design philosophy by allowing the system to continue serving requests while replicas synchronize.

Strong consistency introduces additional coordination to provide fresher data, but only within a single AWS Region.

---

# Global Tables

Global Tables replicate data across AWS Regions.

Example:

```text
Virginia

↓

London

↓

Singapore
```

A write occurring in Virginia takes time to reach the other Regions.

Because of network latency across continents, Global Tables always provide:

```text
Eventually Consistent Reads
```

Strong consistency across continents would require waiting for inter-Region synchronization, dramatically increasing latency and reducing availability.

---

# Cost Comparison

| Read Type | Capacity Cost | Latency | Freshness |
|------------|--------------:|---------|-----------|
| Eventually Consistent | 0.5 RCU (per 4 KB read) | Lower | May return slightly stale data |
| Strongly Consistent | 1 RCU (per 4 KB read) | Higher | Always latest committed value |

Choosing strong consistency everywhere unnecessarily increases cost and reduces scalability.

---

# Best Practices

- Use eventually consistent reads by default.
- Enable strong consistency only where stale data is unacceptable.
- Understand business requirements before choosing a consistency model.
- Avoid assuming every application requires the latest value immediately.
- Test applications that rely on immediate read-after-write behavior.

---

# Common Mistakes

## Using Strong Consistency Everywhere

Many developers assume stronger guarantees are always better.

In reality, this often increases cost without providing meaningful business value.

---

## Assuming Eventual Consistency Means Data Loss

Eventually consistent reads do **not** mean writes are lost.

They simply mean replicas may require a short period to synchronize.

All successful writes remain durable.

---

## Expecting GSIs to Support Strong Consistency

Global Secondary Indexes are always eventually consistent.

Applications requiring immediate consistency should query the base table instead.

---

## Ignoring User Experience

Some applications can tolerate slightly stale data.

Others cannot.

Consistency requirements should always be driven by business needs rather than technical preference.

---

# Interview Notes

A common interview question is:

> **If eventually consistent reads can return stale data, why are they the default?**

Because most applications prioritize low latency, scalability, and cost over immediate consistency.

For many workloads—such as product catalogs, news feeds, recommendation engines, analytics dashboards, and social media—a delay of a few milliseconds is unnoticeable to users.

Using eventual consistency allows DynamoDB to serve more requests with lower latency while consuming half the read capacity compared to strongly consistent reads.

---

# Key Takeaways

- Replication improves availability but introduces temporary consistency delays.
- DynamoDB supports Eventually Consistent and Strongly Consistent Reads.
- Eventually consistent reads are the default because they are faster, cheaper, and more scalable.
- Strongly consistent reads guarantee the latest committed value but consume twice the read capacity.
- Strong consistency is available only on base tables and Local Secondary Indexes.
- Global Secondary Indexes and Global Tables always use eventual consistency.
- Choosing the appropriate consistency model is a business decision that balances correctness, performance, scalability, and cost.