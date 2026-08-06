# Partition Strategy

## Overview

One of the most important decisions when creating a Kafka topic is determining **how many partitions it should have** and **how messages should be distributed among them**.

Partitions directly affect:

- Parallel processing
- Consumer scalability
- Producer throughput
- Message ordering
- Storage distribution
- Future scalability

Unlike many Kafka configurations, increasing or decreasing partitions after a system goes into production can have significant consequences. Therefore, a good partition strategy should be planned before deploying an application.

---

# What is a Partition?

A partition is an ordered, append-only log within a Kafka topic.

Example:

```text
Orders Topic

├── Partition 0
├── Partition 1
├── Partition 2
└── Partition 3
```

Each partition stores its own sequence of messages.

---

# Why Topics are Partitioned

Without partitions:

```text
Orders Topic

↓

One Log

↓

One Consumer
```

Processing is limited.

With partitions:

```text
Orders Topic

├── P0
├── P1
├── P2
└── P3

↓

Multiple Consumers
```

Workload can be processed in parallel.

---

# Benefits of Partitioning

Partitioning provides:

- Horizontal scalability
- Parallel consumption
- Higher throughput
- Load balancing
- Better resource utilization
- Fault tolerance

Most of Kafka's scalability comes from partitions.

---

# Partition Architecture

```text
                 Orders Topic
                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼
  Partition 0    Partition 1    Partition 2
      │               │               │
      ▼               ▼               ▼
   Broker A       Broker B       Broker C
```

Partitions may be distributed across multiple brokers.

---

# Message Distribution

When a producer sends a message, Kafka decides which partition will receive it.

Decision factors:

- Message Key
- Partition Count
- Partitioner

Workflow:

```text
Producer

↓

Partitioner

↓

Partition

↓

Kafka Broker
```

---

# Partitioning Without a Key

Suppose the producer sends messages without a key.

```text
Producer

↓

Key = NULL
```

Kafka distributes records across partitions.

Example:

```text
Message 1

↓

P0

Message 2

↓

P2

Message 3

↓

P1

Message 4

↓

P3
```

Modern Kafka producers use a sticky partitioning strategy to improve batching efficiency.

---

# Partitioning With a Key

Suppose:

```text
Customer ID = 1025
```

Kafka computes:

```text
Hash(Key)

↓

Partition
```

Every message with the same key is routed to the same partition.

Example:

```text
Customer 1025

↓

Partition 1
```

This preserves ordering for that key.

---

# Hash-Based Partitioning

Kafka uses a hash function internally.

Simplified:

```text
Hash(Key)

%

Number of Partitions

↓

Partition
```

Example:

```text
Hash(1025)

↓

8

↓

Partition 0
```

Applications normally do not implement this manually.

---

# Why Message Keys Matter

Suppose an order goes through several stages.

```text
Order Created

↓

Order Paid

↓

Order Packed

↓

Order Delivered
```

Using:

```text
Key = Order ID
```

All events reach the same partition.

Ordering is preserved.

---

# Ordering Guarantees

Kafka guarantees ordering only within a partition.

Example:

```text
Partition 2

↓

Event A

↓

Event B

↓

Event C
```

Kafka guarantees:

```text
A

↓

B

↓

C
```

Across different partitions, no ordering guarantee exists.

---

# Choosing the Number of Partitions

The partition count should consider:

- Expected throughput
- Consumer parallelism
- Future growth
- Broker count
- Storage capacity

There is no universal "correct" number.

---

# Too Few Partitions

Example:

```text
Orders Topic

↓

2 Partitions
```

Problems:

- Limited scalability
- Low parallelism
- Consumers become bottlenecks

---

# Too Many Partitions

Example:

```text
Orders Topic

↓

5000 Partitions
```

Problems:

- Increased metadata
- More open files
- Higher memory usage
- Longer leader elections
- Slower rebalancing

Partitions are not free.

---

# Consumer Parallelism

Maximum parallelism equals the number of partitions.

Example:

```text
Topic

↓

8 Partitions
```

Maximum active consumers:

```text
8
```

Adding a ninth consumer:

```text
Idle Consumer
```

---

# Producer Throughput

Multiple partitions allow producers to write in parallel.

```text
Producer

↓

P0

↓

Broker A

----------------

Producer

↓

P1

↓

Broker B
```

Higher partition counts generally increase write throughput.

---

# Broker Distribution

Suppose:

```text
Topic

6 Partitions
```

Kafka distributes them.

```text
Broker A

P0

P3

----------------

Broker B

P1

P4

----------------

Broker C

P2

P5
```

Storage and workload are balanced across brokers.

---

# Hot Partitions

A hot partition receives significantly more traffic than others.

Example:

```text
P0

90%

Traffic

----------------

P1

5%

----------------

P2

5%
```

Causes:

- Poor key selection
- Uneven hashing
- Popular customers

Hot partitions reduce overall throughput.

---

# Choosing Good Message Keys

Good keys:

```text
Order ID

Customer ID

Invoice ID

Shipment ID
```

Poor keys:

```text
Country

Status

Region

Boolean Value
```

Poor keys create uneven partition distribution.

---

# Partition Growth

Adding partitions later is possible.

```text
4 Partitions

↓

Increase

↓

8 Partitions
```

However:

- Existing messages remain unchanged.
- Key-to-partition mapping changes for future records.
- Ordering across old and new records may be affected.

Increasing partitions should be planned carefully.

---

# Partition Strategy Workflow

```text
Estimate Traffic

↓

Estimate Consumers

↓

Estimate Future Growth

↓

Choose Partition Count

↓

Choose Message Key

↓

Deploy
```

---

# Real-World Example

An e-commerce platform.

Topic:

```text
orders
```

Configuration:

```text
24 Partitions
```

Reason:

- Twelve order-processing consumers
- Future expansion
- High order volume

Partition key:

```text
Order ID
```

Benefits:

- Parallel processing
- Ordered events per order
- Balanced workload

---

# Recommended Partition Planning

| Expected Traffic | Suggested Starting Point |
|------------------|-------------------------:|
| Development | 1–3 Partitions |
| Small Production | 3–6 Partitions |
| Medium Scale | 12–24 Partitions |
| Large Enterprise | 50+ Partitions |

Actual partition counts should be determined through capacity planning and benchmarking.

---

# Best Practices

- Design partitions for future growth.
- Choose keys with high cardinality.
- Keep related events in the same partition.
- Monitor partition distribution.
- Avoid creating thousands of partitions without justification.
- Benchmark throughput before increasing partition counts.
- Remember that maximum consumer parallelism equals the number of partitions.

---

# Common Mistakes

- Using a single partition for high-volume workloads.
- Creating excessive partitions "just in case."
- Choosing low-cardinality message keys.
- Assuming Kafka guarantees ordering across partitions.
- Increasing partitions without understanding the effect on key distribution.
- Ignoring hot partitions.

---

# Summary

Partition strategy is one of the most important architectural decisions in Kafka. The number of partitions determines the maximum parallelism, influences throughput, and affects how workloads are distributed across brokers and consumers. A well-designed partition strategy balances scalability, ordering requirements, and operational efficiency while avoiding hot partitions and unnecessary complexity. Careful planning of partition counts and message keys helps ensure a Kafka deployment remains scalable as data volume and consumer demand grow.

---

# Key Takeaways

- Partitions enable Kafka's horizontal scalability and parallel processing.
- The number of partitions determines the maximum consumer parallelism.
- Message keys determine which partition stores a record.
- Kafka guarantees ordering only within a partition.
- Good message keys distribute data evenly while preserving ordering where needed.
- Too few partitions limit scalability; too many increase operational overhead.
- Hot partitions reduce cluster efficiency and should be avoided.
- Partition strategy should be based on expected workload, future growth, and benchmarking rather than arbitrary numbers.