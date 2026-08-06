# Offsets

## Overview

An **Offset** is a unique sequential number assigned to every message within a Kafka partition. It acts as the message's position inside the partition and allows consumers to track which messages have already been processed.

Offsets are one of Kafka's most important concepts because they enable:

- Reliable message processing
- Message replay
- Consumer recovery
- Fault tolerance
- Independent consumers

Unlike traditional message queues that remove messages after they are consumed, Kafka retains messages for a configurable period. Offsets allow consumers to determine where to start reading without affecting other consumers.

---

# What is an Offset?

Every message written to a partition receives the next available offset.

Example:

```text
Partition 0

Offset 0  → Order Created
Offset 1  → Payment Completed
Offset 2  → Inventory Updated
Offset 3  → Email Sent
Offset 4  → Invoice Generated
```

Offsets always increase sequentially.

Once assigned, an offset never changes.

---

# Offsets are Partition-Specific

Offsets are **not unique across the entire Kafka cluster**.

Each partition starts counting from zero.

Example:

```text
Orders Topic

Partition 0

Offset 0
Offset 1
Offset 2

---------------------

Partition 1

Offset 0
Offset 1
Offset 2
```

Both partitions have an Offset 0.

The unique identifier of a message is:

```text
Topic
+
Partition
+
Offset
```

For example:

```text
orders
Partition 2
Offset 145
```

---

# Why Do We Need Offsets?

Suppose a consumer has already processed the first four messages.

```text
Partition

Offset 0 ✅

Offset 1 ✅

Offset 2 ✅

Offset 3 ✅

Offset 4 ⏳

Offset 5

Offset 6
```

Instead of reading everything again, Kafka tells the consumer:

> Start from Offset 4.

This makes message consumption efficient.

---

# How Consumers Use Offsets

Consumers continuously poll Kafka for new messages.

Example:

```text
Consumer

↓

Read Offset 0

↓

Read Offset 1

↓

Read Offset 2

↓

Commit Offset

↓

Read Offset 3
```

After processing messages, the consumer records its progress by committing the latest processed offset.

---

# Consumer Position

Every consumer has its own position.

Example:

```text
Partition

Offset 0

Offset 1

Offset 2

Offset 3

Offset 4

Offset 5

Offset 6
```

Consumer A:

```text
Current Position

↓

Offset 5
```

Consumer B:

```text
Current Position

↓

Offset 2
```

Both consumers can read the same partition independently.

---

# Offset Progression

As new messages arrive:

```text
Offset 0

Offset 1

Offset 2

Offset 3

Offset 4

Offset 5

Offset 6

Offset 7

Offset 8
```

Consumers simply continue reading from their last committed offset.

---

# Offset Commit

After successfully processing messages, a consumer commits its offset.

Example:

```text
Read Message

↓

Process Message

↓

Commit Offset
```

This tells Kafka:

> "Everything before this offset has been successfully processed."

If the consumer restarts, it resumes from the committed offset.

---

# Auto Offset Commit

Kafka can automatically commit offsets.

Example configuration:

```properties
enable.auto.commit=true
```

Workflow:

```text
Read

↓

Process

↓

Kafka Automatically Commits Offset
```

Advantages:

- Easy to configure
- Less code
- Suitable for simple applications

Disadvantages:

- Risk of message loss if processing fails before completion.

---

# Manual Offset Commit

Applications can manually decide when to commit offsets.

Workflow:

```text
Read Message

↓

Business Logic

↓

Database Update

↓

Commit Offset
```

Advantages:

- Better reliability
- More control
- Suitable for production systems

Disadvantages:

- Slightly more complex implementation

---

# Consumer Restart Example

Suppose the consumer processed messages until Offset 120.

```text
Offset 118

Offset 119

Offset 120 ✅

Offset 121

Offset 122
```

The consumer crashes.

After restarting:

```text
Resume From

↓

Offset 121
```

Previously processed messages do not need to be processed again (assuming Offset 120 was committed).

---

# Message Replay

One of Kafka's biggest advantages is the ability to replay old events.

Example:

```text
Offset 0

Offset 1

Offset 2

Offset 3

Offset 4

Offset 5
```

Instead of continuing from Offset 6, a consumer can intentionally start from Offset 0.

```text
Consumer

↓

Read Offset 0 Again
```

Replay is commonly used for:

- Rebuilding search indexes
- Reprocessing analytics
- Recovering from application bugs
- Testing new consumers
- Data migration

---

# Earliest vs Latest Offset

Consumers can decide where to start reading.

## Earliest

```text
Offset 0

↓

Read Everything
```

Configuration:

```properties
auto.offset.reset=earliest
```

---

## Latest

```text
Current End

↓

Read Only New Messages
```

Configuration:

```properties
auto.offset.reset=latest
```

---

# Offset Retention

Kafka stores committed offsets separately from message data.

If a consumer remains inactive for a long period, committed offsets may eventually expire depending on broker configuration.

If no valid committed offset exists, Kafka follows the `auto.offset.reset` policy.

---

# Offsets and Consumer Groups

Offsets are tracked **per Consumer Group**, not per topic.

Example:

```text
Orders Topic

Consumer Group A

Committed Offset = 200

------------------------

Consumer Group B

Committed Offset = 75
```

Each consumer group progresses independently.

This allows multiple applications to process the same topic without interfering with each other.

---

# Offset vs Partition

These concepts are often confused.

| Partition | Offset |
|-----------|--------|
| Divides a topic into multiple segments | Identifies a message inside a partition |
| Used for scalability | Used for tracking progress |
| One topic can have many partitions | Every partition has its own offsets |
| Physical storage unit | Sequential message identifier |

---

# Advantages of Offsets

- Reliable processing
- Consumer recovery
- Replay capability
- Independent consumers
- Fault tolerance
- Flexible consumption strategies

---

# Common Mistakes

- Assuming offsets are globally unique.
- Confusing offsets with partitions.
- Committing offsets before processing finishes.
- Forgetting to commit offsets when using manual commit.
- Assuming deleting a message changes other offsets.

---

# Best Practices

- Use manual commits for critical business workflows.
- Commit offsets only after successful processing.
- Understand the difference between `earliest` and `latest`.
- Monitor consumer lag to identify processing delays.
- Use replay carefully in production environments.

---

# Summary

Offsets are sequential identifiers assigned to every message within a Kafka partition. They allow consumers to track processing progress, recover after failures, and replay historical events when necessary. Because offsets are managed independently for each consumer group, multiple applications can consume the same topic without affecting one another. Understanding offsets is fundamental to building reliable and fault-tolerant Kafka applications.

---

# Key Takeaways

- Every message in a partition has a unique sequential offset.
- Offsets are unique only within a partition.
- Consumers use offsets to track processed messages.
- Offsets enable recovery after consumer failures.
- Manual commits provide greater control than automatic commits.
- Multiple consumer groups maintain independent offsets.
- Kafka supports replaying historical events using offsets.
- Proper offset management is essential for reliable message processing.