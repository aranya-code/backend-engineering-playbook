# Message Ordering

## Overview

In distributed systems, the order in which events are processed is often just as important as the events themselves.

Consider the following sequence of events for an online order:

1. Order Created
2. Payment Completed
3. Order Shipped
4. Order Delivered

If these events are processed in a different order, the application may behave incorrectly.

Apache Kafka provides **strong message ordering guarantees**, but there is an important limitation:

> **Kafka guarantees message ordering only within a single partition.**

Understanding this concept is essential when designing Kafka topics, choosing message keys, and deciding the number of partitions.

---

# Why Message Ordering Matters

Consider a banking system.

The following events occur:

```text
Deposit ₹5,000

↓

Withdraw ₹2,000

↓

Transfer ₹1,000
```

If Kafka processes them in this order:

```text
Withdraw

↓

Deposit

↓

Transfer
```

The account balance becomes incorrect.

Correct ordering is critical for many business applications.

---

# Ordering Inside a Partition

Kafka stores messages sequentially inside a partition.

Example:

```text
Orders Topic

Partition 0

Offset 0 → Order Created

Offset 1 → Payment Completed

Offset 2 → Order Packed

Offset 3 → Order Shipped

Offset 4 → Order Delivered
```

Consumers always read them in the same order.

```text
Order Created

↓

Payment Completed

↓

Order Packed

↓

Order Shipped

↓

Order Delivered
```

Ordering is guaranteed.

---

# Why Kafka Preserves Ordering

Kafka uses an append-only log.

Every new message is appended to the end of the partition.

```text
Offset

0

1

2

3

4

5
```

Messages are never inserted in the middle.

They are never reordered.

This simple design makes ordering reliable and efficient.

---

# Ordering Across Multiple Partitions

Suppose a topic has three partitions.

```text
Orders Topic

Partition 0

Order A

Order D

Order G

---------------------

Partition 1

Order B

Order E

Order H

---------------------

Partition 2

Order C

Order F

Order I
```

Kafka guarantees ordering inside each partition.

However, it does **not** guarantee the global order across all partitions.

For example, consumers may process:

```text
Order A

↓

Order C

↓

Order B
```

This is perfectly valid.

---

# Why Ordering Across Partitions is Impossible

Partitions are processed independently.

```text
Partition 0

↓

Consumer 1

-------------------

Partition 1

↓

Consumer 2

-------------------

Partition 2

↓

Consumer 3
```

Since multiple consumers work simultaneously, Kafka cannot guarantee a global ordering.

This trade-off allows Kafka to achieve massive scalability.

---

# Message Keys Preserve Ordering

The primary purpose of message keys is to ensure related events remain in the same partition.

Example:

```text
Customer 101

↓

Order Created

↓

Payment Completed

↓

Order Shipped
```

Using:

```text
Key = Customer ID
```

Kafka routes every event for Customer 101 to the same partition.

```text
Customer 101

↓

Partition 2
```

Ordering is preserved.

---

# Example Without Keys

Suppose no key is provided.

Kafka distributes messages automatically.

```text
Order Created

↓

Partition 0

----------------

Payment Completed

↓

Partition 2

----------------

Order Shipped

↓

Partition 1
```

Different consumers process different partitions.

The final processing order becomes unpredictable.

---

# Example With Keys

Now use:

```text
Key = Order ID
```

Kafka calculates:

```text
Hash(Order ID)

↓

Partition 1
```

Every event goes to Partition 1.

```text
Partition 1

Order Created

↓

Payment Completed

↓

Order Packed

↓

Order Shipped
```

Ordering is maintained.

---

# Real-World Example

Consider an inventory system.

Events:

```text
Stock Added

↓

Stock Reserved

↓

Stock Sold

↓

Stock Released
```

If these events arrive out of order:

```text
Stock Sold

↓

Stock Added
```

Inventory becomes inconsistent.

Using:

```text
Key = Product ID
```

ensures every inventory event for the same product stays in one partition.

---

# Ordering and Consumer Groups

Consumer groups also affect ordering.

Suppose:

```text
Partition 0

↓

Consumer A
```

Since only one consumer processes the partition:

```text
Message 1

↓

Message 2

↓

Message 3
```

Ordering is preserved.

Kafka never assigns the same partition to two consumers within the same consumer group.

---

# Scaling vs Ordering

This is one of Kafka's biggest design trade-offs.

### More Partitions

```text
More Partitions

↓

Higher Throughput

↓

Less Global Ordering
```

### Fewer Partitions

```text
Fewer Partitions

↓

Lower Throughput

↓

Stronger Ordering
```

Designers must balance scalability and ordering requirements.

---

# Choosing the Right Key

A good message key should:

- Represent a business entity.
- Preserve required ordering.
- Distribute traffic evenly.
- Avoid creating hot partitions.

Examples:

Good:

```text
Order ID

Customer ID

Account Number

Invoice ID

Device ID
```

Poor:

```text
Country

City

Region

Status
```

Low-cardinality keys may overload a single partition.

---

# Ordering and Retries

Producer retries can affect ordering if multiple requests are in flight.

Modern Kafka producers prevent this by enabling idempotence.

Recommended configuration:

```properties
enable.idempotence=true
max.in.flight.requests.per.connection=5
acks=all
```

These settings help preserve ordering during transient failures.

---

# Ordering and Exactly Once

Exactly Once processing guarantees:

- No duplicate messages.
- No message loss.

However, ordering still depends on partitions.

Exactly Once **does not** guarantee ordering across multiple partitions.

---

# Common Use Cases Requiring Ordering

Ordering is critical for:

- Banking transactions
- Payment processing
- Inventory management
- Order lifecycle
- User account updates
- Financial ledgers
- Workflow state transitions

Ordering is less critical for:

- Log aggregation
- Metrics collection
- Analytics events
- Monitoring systems

---

# Best Practices

- Use message keys whenever ordering matters.
- Choose keys based on business entities.
- Avoid unnecessary partitions if strict ordering is required.
- Enable idempotent producers in production.
- Understand that ordering is guaranteed only within a partition.
- Design topics with both scalability and ordering requirements in mind.

---

# Common Mistakes

- Assuming Kafka guarantees global ordering.
- Sending related events without message keys.
- Using random keys when ordering is important.
- Creating too many partitions without considering ordering.
- Confusing delivery guarantees with ordering guarantees.

---

# Summary

Kafka guarantees message ordering within a single partition by storing messages in an append-only log. Related events should use the same message key so they are consistently routed to the same partition. While increasing the number of partitions improves scalability and throughput, it removes any guarantee of global ordering across the topic. Designing an effective partitioning and key strategy is therefore essential for balancing performance and correctness.

---

# Key Takeaways

- Kafka guarantees message ordering only within a partition.
- Messages are stored sequentially using increasing offsets.
- Message keys ensure related events are routed to the same partition.
- Ordering across multiple partitions is not guaranteed.
- Consumer groups preserve ordering because each partition is assigned to only one consumer within the group.
- More partitions improve scalability but reduce global ordering guarantees.
- Proper key selection is essential for applications that depend on event order.
- Ordering requirements should be considered when designing Kafka topics and partition strategies.