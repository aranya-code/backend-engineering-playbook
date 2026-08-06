# Consumer Groups

## Overview

A **Consumer Group** is a collection of one or more consumers working together to process messages from a Kafka topic. Consumer groups allow Kafka applications to scale horizontally while ensuring that each message is processed only once within the group.

Consumer groups are one of Kafka's most powerful features because they combine **parallel processing**, **fault tolerance**, and **automatic load balancing**.

Without consumer groups, building scalable event-driven applications would be significantly more difficult.

---

# What is a Consumer Group?

A Consumer Group is identified by a unique **Group ID**.

Example:

```text
group.id = order-processing-group
```

Every consumer that shares the same Group ID belongs to the same group.

Example:

```text
Consumer A

Consumer B

Consumer C

↓

Consumer Group

order-processing-group
```

Kafka treats these consumers as a single logical unit.

---

# Why Do We Need Consumer Groups?

Imagine an e-commerce application receiving millions of orders every day.

If only one consumer processes every order:

```text
Orders Topic

↓

Consumer
```

The consumer eventually becomes a bottleneck.

Instead, Kafka allows multiple consumers to work together.

```text
Orders Topic

↓

Consumer Group

├── Consumer 1
├── Consumer 2
├── Consumer 3
└── Consumer 4
```

Now the workload is shared.

---

# Consumer Group Architecture

```text
                Orders Topic

      ┌──────────┬──────────┬──────────┐
      │          │          │          │
      ▼          ▼          ▼          ▼
     P0         P1         P2         P3

      │          │          │          │

      └──────────┬──────────┬──────────┘
                 ▼

          Consumer Group

     ┌────────┬────────┐
     │        │        │
     ▼        ▼        ▼
 Consumer1 Consumer2 Consumer3
```

Kafka automatically distributes partitions among consumers.

---

# One Partition, One Consumer

Within a Consumer Group:

- One partition can be assigned to only one consumer.
- One consumer can process multiple partitions.

Example:

```text
Orders Topic

P0

P1

P2

P3

↓

Consumer Group

Consumer 1 → P0, P1

Consumer 2 → P2

Consumer 3 → P3
```

This guarantees that messages from a partition are processed by only one consumer at a time.

---

# Why Can't Two Consumers Read the Same Partition?

Suppose two consumers process the same partition simultaneously.

```text
Partition 0

↓

Consumer A

Consumer B
```

Problems include:

- Duplicate processing
- Inconsistent data
- Race conditions
- Incorrect business logic

Kafka avoids these issues by assigning a partition to only one consumer within a group.

---

# Consumer Group Example

Suppose a topic has four partitions.

```text
Orders Topic

P0

P1

P2

P3
```

And there are two consumers.

```text
Consumer Group

Consumer 1

Consumer 2
```

Kafka may assign partitions like this.

```text
Consumer 1

P0

P2

------------------

Consumer 2

P1

P3
```

Each consumer processes its assigned partitions independently.

---

# More Consumers Than Partitions

Suppose:

- Topic has 3 partitions
- Consumer Group has 5 consumers

```text
Partitions

P0

P1

P2

Consumers

C1

C2

C3

C4

C5
```

Assignment:

```text
C1 → P0

C2 → P1

C3 → P2

C4 → Idle

C5 → Idle
```

Kafka cannot assign more than one consumer to a partition.

Extra consumers remain idle until additional partitions become available.

---

# More Partitions Than Consumers

Suppose:

- Topic has 8 partitions
- Consumer Group has 3 consumers

Example assignment:

```text
Consumer 1

P0

P1

P2

----------------

Consumer 2

P3

P4

P5

----------------

Consumer 3

P6

P7
```

Consumers can process multiple partitions simultaneously.

---

# Consumer Groups Enable Parallelism

Without consumer groups:

```text
Orders Topic

↓

Consumer

↓

Process Every Message
```

With consumer groups:

```text
Orders Topic

↓

Consumer Group

├── Consumer 1
├── Consumer 2
├── Consumer 3
└── Consumer 4
```

Multiple consumers process messages simultaneously, increasing throughput.

---

# Independent Consumer Groups

Multiple consumer groups can subscribe to the same topic.

```text
Orders Topic

        │

 ┌──────┼───────────┐

 ▼      ▼           ▼

Inventory Group

Shipping Group

Analytics Group
```

Each group receives every message.

Example:

```text
Order Created

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service
```

The groups do not affect one another.

---

# Consumer Group Offsets

Offsets are maintained separately for each consumer group.

Example:

```text
Orders Topic

Group A

Offset = 120

-------------------

Group B

Offset = 340

-------------------

Group C

Offset = 15
```

Each group tracks its own progress independently.

---

# Consumer Failure

Suppose Consumer 2 crashes.

Before failure:

```text
Consumer 1 → P0

Consumer 2 → P1

Consumer 3 → P2
```

After failure:

```text
Consumer 1 → P0

Consumer 3 → P1

Consumer 3 → P2
```

Kafka automatically redistributes partitions among the remaining consumers.

This process is called **rebalancing**.

---

# Rebalancing

A rebalance occurs whenever the membership of a consumer group changes.

Common reasons include:

- Consumer joins
- Consumer leaves
- Consumer crashes
- Topic partitions increase

Example:

Before:

```text
C1 → P0

C2 → P1
```

After a new consumer joins:

```text
C1 → P0

C2 → P1

C3 → P2
```

Kafka redistributes the workload automatically.

---

# Scaling Consumer Groups

Scaling is straightforward.

Increase consumers.

```text
1 Consumer

↓

2 Consumers

↓

4 Consumers

↓

8 Consumers
```

Or increase partitions.

```text
3 Partitions

↓

6 Partitions

↓

12 Partitions
```

Both approaches increase processing capacity.

---

# Consumer Groups vs Multiple Consumers

These concepts are often confused.

| Multiple Independent Consumers | Consumer Group |
|--------------------------------|----------------|
| Every consumer receives every message | Messages are shared among consumers |
| Used when every application needs all events | Used for parallel processing |
| Independent offsets | Shared workload |
| No load balancing | Automatic partition assignment |

---

# Best Practices

- Use one consumer group per application.
- Choose meaningful Group IDs.
- Match the number of partitions to expected consumer scalability.
- Monitor consumer lag.
- Handle rebalances gracefully.
- Keep message processing idempotent.
- Avoid frequent consumer restarts.

---

# Common Mistakes

- Creating more consumers than partitions.
- Assuming every consumer receives every message.
- Forgetting that offsets are tracked per group.
- Ignoring consumer lag.
- Not handling rebalance events.
- Changing Group IDs unintentionally, causing consumers to reprocess data.

---

# Summary

Consumer groups allow multiple consumers to work together as a single logical unit, enabling Kafka to process messages in parallel while ensuring each partition is handled by only one consumer within the group. Kafka automatically assigns partitions, manages failures through rebalancing, and maintains separate offsets for each consumer group. Proper use of consumer groups is essential for building scalable, fault-tolerant, and high-throughput event-driven systems.

---

# Key Takeaways

- A Consumer Group is a collection of consumers sharing the same Group ID.
- Kafka assigns each partition to only one consumer within a group.
- One consumer can process multiple partitions.
- Extra consumers remain idle if there are more consumers than partitions.
- Multiple consumer groups can independently consume the same topic.
- Offsets are maintained separately for each consumer group.
- Kafka automatically redistributes partitions during consumer failures or membership changes.
- Consumer groups are the foundation of horizontal scalability in Kafka.
```