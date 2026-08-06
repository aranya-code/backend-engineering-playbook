# Partitions

## Overview

Partitions are one of the most important concepts in Apache Kafka and are the primary reason Kafka can scale to handle millions of messages per second.

A **partition** is an ordered, immutable sequence of messages within a topic. Instead of storing all messages in a single location, Kafka divides a topic into multiple partitions, allowing data to be distributed across multiple brokers.

Partitions enable:

- Horizontal scalability
- Parallel processing
- Load balancing
- Fault tolerance
- High throughput

Without partitions, Kafka would not be able to efficiently process massive volumes of data.

---

# What is a Partition?

A partition is a physical subdivision of a topic.

Consider the following topic:

```text
orders
```

If it contains only one partition:

```text
orders

┌────────────────────────┐
│ Partition 0            │
└────────────────────────┘
```

Every message is stored in the same partition.

As message volume grows, this quickly becomes a bottleneck.

Instead, Kafka allows topics to be divided into multiple partitions.

```text
orders

┌────────────┐
│Partition 0 │
└────────────┘

┌────────────┐
│Partition 1 │
└────────────┘

┌────────────┐
│Partition 2 │
└────────────┘

┌────────────┐
│Partition 3 │
└────────────┘
```

Each partition stores part of the topic's data.

---

# Why Do We Need Partitions?

Imagine an e-commerce platform processing:

- 10 orders per day

A single partition is sufficient.

Now imagine:

- 10 million orders per day

A single partition becomes a bottleneck because:

- Only one broker stores the data.
- Consumers process messages sequentially.
- Producer throughput is limited.

Partitions solve this by distributing work.

```text
Producer

          │

          ▼

      orders Topic

 ┌──────┬──────┬──────┬──────┐
 │ P0   │ P1   │ P2   │ P3   │
 └──────┴──────┴──────┴──────┘
```

Now producers and consumers can work in parallel.

---

# Partition Distribution

A topic's partitions may be stored on different brokers.

Example:

```text
Kafka Cluster

Broker 1

Partition 0

Partition 3

-------------------------

Broker 2

Partition 1

Partition 4

-------------------------

Broker 3

Partition 2

Partition 5
```

This distributes:

- Storage
- Network traffic
- CPU utilization

across the cluster.

---

# Messages Inside a Partition

Messages are always stored in the order they arrive.

Example:

```text
Partition 0

Offset 0

Order #101

---------------

Offset 1

Order #102

---------------

Offset 2

Order #103
```

Kafka appends new messages to the end of the partition.

Messages are never inserted into the middle.

---

# Ordering Guarantee

Kafka guarantees message ordering **only within a single partition**.

Example:

```text
Partition 0

Order 1

Order 2

Order 3

Order 4
```

Consumers will always read:

```text
Order 1

↓

Order 2

↓

Order 3

↓

Order 4
```

The order is preserved.

---

# Ordering Across Partitions

Suppose the topic has three partitions.

```text
orders

P0

Order 1

Order 4

Order 7

-----------------

P1

Order 2

Order 5

Order 8

-----------------

P2

Order 3

Order 6

Order 9
```

Kafka does **not** guarantee the overall ordering across different partitions.

Only the ordering inside each partition is guaranteed.

This is one of the most important interview concepts.

---

# How Kafka Chooses a Partition

Kafka determines the destination partition using one of three approaches.

## 1. Message Key

If a key is provided:

```text
Customer ID = 105
```

Kafka computes:

```text
Hash(Key) % Number of Partitions
```

The same key always maps to the same partition.

Example:

```text
Customer 101

↓

Partition 2

---------------

Customer 101

↓

Partition 2

---------------

Customer 101

↓

Partition 2
```

This preserves ordering for that key.

---

## 2. Round Robin

If no key is supplied:

```text
Message 1 → P0

Message 2 → P1

Message 3 → P2

Message 4 → P0

Message 5 → P1
```

Kafka distributes messages evenly.

This improves load balancing.

---

## 3. Custom Partitioner

Applications can implement custom partitioning logic.

Example:

```text
Premium Customers

↓

Partition 0

Regular Customers

↓

Partition 1

International Orders

↓

Partition 2
```

Custom partitioners are useful for specialized business requirements.

---

# Producer and Partitions

A producer sends messages to a topic.

Kafka decides which partition receives each message.

```text
Producer

      │

      ▼

Orders Topic

 ┌──────┬──────┬──────┐
 │ P0   │ P1   │ P2   │
 └──────┴──────┴──────┘
```

The producer does not directly write to every broker.

It communicates with the leader of the target partition.

---

# Consumer and Partitions

Consumers read messages from partitions.

Example:

```text
Orders Topic

P0

P1

P2

P3

      │

Consumer Group

      │

 ┌──────────┐
 │Consumer 1│
 └──────────┘

 ┌──────────┐
 │Consumer 2│
 └──────────┘
```

Kafka automatically distributes partitions among consumers in the same group.

---

# Parallel Processing

Partitions enable multiple consumers to process data simultaneously.

```text
Orders Topic

P0 → Consumer 1

P1 → Consumer 2

P2 → Consumer 3

P3 → Consumer 4
```

Without partitions:

```text
Consumer 1

↓

All Messages
```

With partitions:

```text
Consumer 1

Consumer 2

Consumer 3

Consumer 4

↓

Process Messages Simultaneously
```

This dramatically increases throughput.

---

# Choosing the Number of Partitions

There is no universal answer.

It depends on:

- Expected traffic
- Consumer count
- Throughput requirements
- Storage capacity
- Future growth

General guidelines:

| Workload | Suggested Partitions |
|----------|----------------------:|
| Development | 1–3 |
| Small Application | 3–6 |
| Medium Production | 6–12 |
| High Traffic Systems | 12–50+ |

The number should be based on workload rather than arbitrary values.

---

# Can We Increase Partitions Later?

Yes.

Kafka allows increasing the number of partitions.

Example:

```text
Before

P0

P1

P2

↓

After

P0

P1

P2

P3

P4

P5
```

However, increasing partitions changes the key-to-partition mapping.

Applications relying on key ordering should plan partition counts carefully before production.

---

# Advantages of Partitions

- Horizontal scaling
- Better throughput
- Parallel consumers
- Load balancing
- Distributed storage
- High availability
- Efficient resource utilization

---

# Common Mistakes

- Creating only one partition for high-volume topics.
- Creating hundreds of unnecessary partitions.
- Ignoring message ordering requirements.
- Changing partition counts without understanding the impact on key distribution.
- Assuming ordering is guaranteed across all partitions.

---

# Summary

Partitions divide a Kafka topic into smaller, ordered segments that can be distributed across multiple brokers. They are the foundation of Kafka's scalability, enabling producers and consumers to operate in parallel while maintaining message ordering within each partition. Choosing an appropriate partition strategy is one of the most important design decisions in any Kafka deployment.

---

# Key Takeaways

- A partition is a physical subdivision of a Kafka topic.
- Partitions enable horizontal scalability and parallel processing.
- Messages are stored sequentially within a partition.
- Kafka guarantees message ordering only within a single partition.
- Messages with the same key are typically routed to the same partition.
- Topics can span multiple partitions distributed across different brokers.
- Consumers in the same consumer group process different partitions in parallel.
- Proper partition planning is critical for performance, scalability, and maintaining ordering guarantees.