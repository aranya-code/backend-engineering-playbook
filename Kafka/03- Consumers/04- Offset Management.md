# Offset Management

## Overview

One of Kafka's most powerful features is that consumers control **what they have processed** rather than Kafka tracking it automatically.

Kafka achieves this using **Offsets**.

An offset is a unique number assigned to every record within a partition. Consumers use offsets to determine:

- Which messages have already been processed
- Which message should be read next
- Where to resume after a restart
- How to replay historical data

Unlike traditional messaging systems where messages are removed after consumption, Kafka retains messages for a configurable period. Offsets allow multiple consumers to independently read the same data without interfering with one another.

Understanding offset management is essential before learning Auto Commit, Manual Commit, and Delivery Semantics.

---

# What is an Offset?

An offset is a sequential number assigned to every record in a partition.

Example:

```text
Partition 0

Offset 0

Order A

----------------

Offset 1

Order B

----------------

Offset 2

Order C

----------------

Offset 3

Order D
```

Offsets are unique **within a partition**, not across the entire topic.

---

# Why Offsets are Needed

Suppose a consumer reads thousands of records.

How does Kafka know where the consumer should continue?

```text
Consumer

↓

Processed

Offset 105
```

When the consumer polls again:

```text
Next Record

↓

Offset 106
```

Offsets allow consumers to resume processing without rereading old data.

---

# Offset Characteristics

Offsets are:

- Sequential
- Immutable
- Partition-specific
- Assigned by Kafka
- Monotonically increasing

Example:

```text
Offset

0

1

2

3

4

5
```

Offsets never decrease.

---

# Topic with Multiple Partitions

Suppose:

```text
Orders Topic

Partition 0

Offsets

0 1 2 3

----------------

Partition 1

Offsets

0 1 2 3

----------------

Partition 2

Offsets

0 1 2 3
```

Each partition maintains its own offset sequence.

Offset 5 in Partition 0 is unrelated to Offset 5 in Partition 1.

---

# Consumer Position

Every consumer maintains its current position.

Example:

```text
Partition 0

Offset 15

↓

Current Position
```

Next poll:

```text
Offset 16
```

The position moves forward as records are processed.

---

# Offset Progression

Example:

```text
Poll

↓

Offset 100

↓

Process

↓

Commit

↓

Poll

↓

Offset 101
```

Consumers continuously advance through the log.

---

# Current Offset vs Committed Offset

These two concepts are often confused.

### Current Offset

The record currently being processed.

```text
Offset

105
```

---

### Committed Offset

The last successfully saved position.

```text
Committed

104
```

After processing:

```text
Commit

↓

105
```

If the consumer crashes before committing:

```text
Restart

↓

Resume

↓

105
```

The record may be processed again.

---

# Offset Storage

Kafka stores committed offsets internally.

Architecture:

```text
Consumer

↓

Commit Offset

↓

__consumer_offsets Topic
```

Kafka automatically manages this internal topic.

Applications normally do not interact with it directly.

---

# Offset Commit Workflow

```text
Poll Records

↓

Process Records

↓

Commit Offset

↓

Store Offset

↓

Next Poll
```

Committed offsets become the recovery point after failures.

---

# Consumer Restart

Suppose:

```text
Committed Offset

250
```

Consumer crashes.

```text
Crash

↓

Restart

↓

Read Offset

250

↓

Resume

251
```

No manual intervention is required.

---

# Offset and Message Retention

Kafka retains messages independently of offsets.

Example:

```text
Topic

↓

Messages

↓

Retention

7 Days
```

Even after processing:

```text
Messages

Remain Stored
```

Other consumers can still read them.

---

# Multiple Consumers

Different consumer groups maintain independent offsets.

Example:

```text
Orders Topic

↓

Inventory Group

Committed Offset

500

----------------

Analytics Group

Committed Offset

320

----------------

Audit Group

Committed Offset

120
```

Each group progresses independently.

---

# Offset Commit Timing

Processing order:

```text
Poll

↓

Process

↓

Commit
```

Never:

```text
Poll

↓

Commit

↓

Process
```

Committing too early risks message loss.

---

# Offset Example

Suppose a partition contains:

```text
Offset 0

Offset 1

Offset 2

Offset 3

Offset 4
```

Consumer processes:

```text
0

1

2
```

Commit:

```text
Offset 2
```

Next poll begins from:

```text
Offset 3
```

---

# Offset During Failure

Suppose:

```text
Process Offset 8

↓

Crash

↓

No Commit
```

Restart:

```text
Resume

↓

Offset 8
```

Kafka guarantees the record is available again.

---

# Offset and Rebalancing

Suppose a rebalance occurs.

```text
Consumer A

↓

Partition 0

↓

Commit Offset 520
```

Partition moves to Consumer B.

Consumer B starts from:

```text
Offset 521
```

No messages are skipped.

---

# Earliest Offset

When no committed offset exists:

```text
auto.offset.reset=earliest
```

Consumer starts from:

```text
Offset 0
```

Entire topic is read.

---

# Latest Offset

Configuration:

```properties
auto.offset.reset=latest
```

Consumer starts from:

```text
Newest Offset
```

Old messages are skipped.

---

# Offset Management Architecture

```text
               Kafka Topic
      ┌──────────────────────┐
      │ Offset 100           │
      │ Offset 101           │
      │ Offset 102           │
      │ Offset 103           │
      └──────────────────────┘
               │
               ▼
        Kafka Consumer
               │
               ▼
       Process Messages
               │
               ▼
       Commit Offset
               │
               ▼
 __consumer_offsets Topic
```

---

# Offset Management Flow

```text
Poll

↓

Read Offset

↓

Process

↓

Commit

↓

Store Offset

↓

Poll Again
```

This cycle continues throughout the consumer's lifetime.

---

# Real-World Example

An inventory service processes order events.

```text
Offset 250

↓

Reserve Stock

↓

Database Updated

↓

Commit Offset

250
```

If the service crashes afterward:

```text
Restart

↓

Offset 251
```

Processing resumes correctly.

---

# Best Practices

- Commit offsets only after successful processing.
- Monitor committed offsets and consumer lag.
- Understand the difference between current and committed offsets.
- Use manual commits for business-critical applications.
- Keep processing idempotent to handle duplicate deliveries.
- Choose the appropriate `auto.offset.reset` policy.

---

# Common Mistakes

- Confusing offsets with message IDs.
- Assuming offsets are shared across partitions.
- Committing offsets before processing completes.
- Forgetting that each consumer group has independent offsets.
- Assuming Kafka deletes messages after consumption.

---

# Summary

Offset management is the mechanism that enables Kafka consumers to track processing progress and recover from failures. Every record within a partition has a unique sequential offset, and consumers commit offsets after successfully processing records. Kafka stores committed offsets in the internal `__consumer_offsets` topic, allowing consumers to resume from the correct position after restarts or rebalancing. Proper offset management is fundamental to building reliable, fault-tolerant Kafka consumer applications.

---

# Key Takeaways

- Offsets uniquely identify records within a partition.
- Consumers use offsets to track processing progress.
- Current offsets and committed offsets represent different stages of processing.
- Kafka stores committed offsets in the internal `__consumer_offsets` topic.
- Each consumer group maintains its own independent offsets.
- Offsets enable recovery after crashes and rebalancing.
- Messages remain in Kafka even after their offsets are committed.
- Correct offset management is essential for reliable message processing.