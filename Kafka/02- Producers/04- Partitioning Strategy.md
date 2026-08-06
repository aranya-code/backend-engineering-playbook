# Partitioning Strategy

## Overview

One of the most important responsibilities of a Kafka producer is deciding **which partition should store a message**.

This decision is known as the **Partitioning Strategy**.

The partition selected for a message directly affects:

- Scalability
- Throughput
- Message ordering
- Consumer parallelism
- Load balancing
- Fault tolerance

A well-designed partitioning strategy allows Kafka to process millions of messages per second while preserving ordering where required.

Poor partitioning decisions, on the other hand, can lead to hot partitions, uneven workloads, and reduced performance.

---

# What is Partitioning?

Partitioning is the process of determining which partition receives a message.

Suppose a topic has four partitions.

```text
Orders Topic

Partition 0

Partition 1

Partition 2

Partition 3
```

Every message must be written to exactly one of these partitions.

The producer is responsible for making this decision.

---

# Why Partitioning Matters

Imagine an e-commerce platform processing one million orders every day.

Without partitioning:

```text
Orders Topic

↓

Partition 0

↓

Single Consumer
```

Everything is processed sequentially.

Now consider multiple partitions.

```text
Orders Topic

↓

P0

P1

P2

P3
```

Multiple consumers can now process messages simultaneously.

Partitioning enables horizontal scalability.

---

# Producer Partitioning Workflow

```text
Application

↓

Create Producer Record

↓

Is Partition Specified?

↓

Yes

↓

Use That Partition

↓

No

↓

Is Key Present?

↓

Yes

↓

Hash Key

↓

Partition

↓

No

↓

Default Partitioner

↓

Partition
```

Kafka follows this decision process for every message.

---

# Partition Selection Methods

Kafka supports three primary partition selection strategies.

- Explicit Partition
- Key-Based Partitioning
- Default Partitioning

Applications can also implement custom partitioners.

---

# Explicit Partition Selection

The producer can specify the partition directly.

Example:

```text
Producer

↓

Partition 2
```

Every message goes to Partition 2.

Example:

```text
Message A

↓

Partition 2

---------------

Message B

↓

Partition 2
```

Advantages:

- Complete control
- Predictable routing

Disadvantages:

- Easy to create uneven workloads
- Requires application logic

This approach is rarely used unless specific business rules require it.

---

# Key-Based Partitioning

This is the most common strategy.

The producer provides a message key.

Example:

```text
Key

Customer ID = 105
```

Kafka calculates:

```text
Hash(Key)

↓

Partition
```

Formula:

```text
Hash(Key) % Number of Partitions
```

Every message with the same key always reaches the same partition.

---

# Example of Key-Based Routing

Messages:

```text
Customer 101

Order Created

------------------

Customer 101

Payment Completed

------------------

Customer 101

Order Shipped
```

Kafka routes them to:

```text
Partition 2

Order Created

↓

Payment Completed

↓

Order Shipped
```

Ordering is preserved.

---

# Default Partitioning

If no key is supplied:

```text
Key = null
```

Kafka distributes messages automatically.

Example:

```text
Message 1

↓

P0

---------------

Message 2

↓

P1

---------------

Message 3

↓

P2

---------------

Message 4

↓

P3
```

This provides excellent load balancing.

However, ordering for related messages is not guaranteed.

---

# Round-Robin Distribution

Modern Kafka producers typically distribute null-key messages evenly across available partitions.

Example:

```text
Message 1 → P0

Message 2 → P1

Message 3 → P2

Message 4 → P3

Message 5 → P0

Message 6 → P1
```

Every partition receives approximately the same number of messages.

---

# Sticky Partitioner

Modern Kafka producers use a **Sticky Partitioner** for messages without keys.

Instead of switching partitions for every message:

```text
Message 1 → P0

Message 2 → P1

Message 3 → P2
```

Kafka temporarily chooses one partition.

```text
Message 1 → P2

Message 2 → P2

Message 3 → P2

↓

Batch Full

↓

Choose New Partition

↓

P0
```

This improves batching efficiency and increases throughput while still balancing messages over time.

---

# Custom Partitioner

Applications can define their own routing logic.

Example:

```text
Premium Customer

↓

Partition 0

---------------------

Standard Customer

↓

Partition 1

---------------------

International Customer

↓

Partition 2
```

Custom partitioners are useful when routing depends on business rules.

---

# Partitioning and Ordering

Partitioning directly affects ordering.

Suppose:

```text
Customer 101

↓

Partition 3
```

Every event for Customer 101 goes to the same partition.

```text
Order Created

↓

Payment Completed

↓

Order Packed

↓

Order Delivered
```

Ordering is guaranteed.

If related events go to different partitions:

```text
Order Created → P0

Payment → P2

Shipment → P1
```

Ordering is no longer guaranteed.

---

# Partitioning and Consumer Groups

Partition selection also determines which consumer processes the message.

Example:

```text
Producer

↓

Partition 1

↓

Consumer Group

↓

Consumer 2
```

The producer does not choose the consumer directly.

It chooses the partition.

Kafka assigns partitions to consumers.

---

# Good Partition Keys

Good keys have:

- High cardinality
- Even distribution
- Stable values
- Business significance

Examples:

```text
Customer ID

Order ID

Invoice ID

Account Number

Device ID
```

These usually distribute messages evenly.

---

# Poor Partition Keys

Poor keys create uneven traffic.

Examples:

```text
Country

Region

Status

Gender
```

Suppose:

```text
Country = India
```

Millions of messages may go to one partition.

Result:

```text
P0

95%

----------------

P1

2%

----------------

P2

2%

----------------

P3

1%
```

This creates a **Hot Partition**.

---

# Hot Partitions

A hot partition receives significantly more traffic than others.

Problems include:

- High CPU usage
- Longer processing times
- Consumer lag
- Reduced throughput
- Uneven broker utilization

Choosing a good key minimizes this problem.

---

# Partition Count and Hashing

Suppose:

```text
Customer 101

↓

Partition 2
```

Now increase the number of partitions.

```text
Before

4 Partitions

↓

After

8 Partitions
```

The hash calculation changes.

Future messages for Customer 101 may now be routed to a different partition.

This is why changing partition counts in production should be planned carefully.

---

# Partitioning Strategies Comparison

| Strategy | Ordering | Load Balancing | Common Usage |
|-----------|----------|----------------|--------------|
| Explicit Partition | Yes | Poor | Special business logic |
| Key-Based | Yes (per key) | Good | Most production systems |
| Default (No Key) | No | Excellent | Logs, metrics, analytics |
| Custom Partitioner | Depends | Depends | Advanced routing |

---

# Best Practices

- Use key-based partitioning whenever ordering matters.
- Choose high-cardinality keys.
- Avoid keys that create hot partitions.
- Use the default partitioner when ordering is unnecessary.
- Monitor partition distribution regularly.
- Plan partition counts before production deployment.
- Use custom partitioners only when standard strategies cannot satisfy business requirements.

---

# Common Mistakes

- Assuming Kafka guarantees ordering across partitions.
- Using the same key for every message.
- Choosing low-cardinality keys.
- Ignoring partition distribution.
- Increasing partition counts without understanding hash remapping.
- Writing custom partitioners unnecessarily.

---

# Summary

Partitioning determines where Kafka stores each message and has a direct impact on scalability, ordering, and throughput. Producers can explicitly choose a partition, use message keys for deterministic routing, rely on Kafka's default partitioner, or implement custom partitioning logic. In most production systems, key-based partitioning provides the best balance between message ordering and load distribution. Careful partition key selection is essential to avoid hot partitions and achieve efficient parallel processing.

---

# Key Takeaways

- Every Kafka message is written to exactly one partition.
- The producer determines the destination partition.
- Kafka supports explicit, key-based, default, and custom partitioning strategies.
- Key-based partitioning preserves ordering for related messages.
- Default partitioning provides excellent load balancing when ordering is not required.
- Sticky partitioning improves batching performance for messages without keys.
- Poor partition keys can create hot partitions and reduce throughput.
- An effective partitioning strategy is critical for building scalable Kafka applications.