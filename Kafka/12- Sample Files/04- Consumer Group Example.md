# Consumer Group Example

## Overview

Consumer Groups are one of Kafka's most powerful features. They enable multiple consumers to work together to process data in parallel while ensuring that each message is processed only once within the same group.

Without Consumer Groups, scaling consumers would be difficult, and duplicate processing would become common.

This chapter explains Consumer Groups through practical examples, showing how Kafka distributes partitions, performs rebalancing, and scales message processing.

---

# What is a Consumer Group?

A Consumer Group is a collection of consumers sharing the workload of one or more topics.

Example:

```text
Orders Topic

↓

Consumer Group

↓

Consumer A

Consumer B

Consumer C
```

Each partition is assigned to exactly one consumer within the group.

---

# Example 1: One Consumer

Topic:

```text
Orders

↓

4 Partitions
```

Consumers:

```text
Consumer Group

↓

Consumer A
```

Assignments:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

One consumer processes all partitions.

---

# Example 2: Two Consumers

Topic:

```text
Orders

↓

4 Partitions
```

Consumers:

```text
Consumer A

Consumer B
```

Assignments:

```text
Consumer A

↓

Partition 0

Partition 1

----------------

Consumer B

↓

Partition 2

Partition 3
```

The workload is shared equally.

---

# Example 3: Four Consumers

Topic:

```text
Orders

↓

4 Partitions
```

Consumers:

```text
Consumer A

Consumer B

Consumer C

Consumer D
```

Assignments:

```text
Partition 0 → Consumer A

Partition 1 → Consumer B

Partition 2 → Consumer C

Partition 3 → Consumer D
```

Each consumer processes one partition.

---

# Maximum Parallelism

Maximum parallelism equals:

```text
Number of Partitions
```

Example:

```text
8 Partitions

↓

Maximum

8 Active Consumers
```

Adding more consumers does not increase throughput.

---

# Example 4: More Consumers Than Partitions

Topic:

```text
4 Partitions
```

Consumers:

```text
Consumer A

Consumer B

Consumer C

Consumer D

Consumer E

Consumer F
```

Assignments:

```text
Consumer A → Partition 0

Consumer B → Partition 1

Consumer C → Partition 2

Consumer D → Partition 3

Consumer E → Idle

Consumer F → Idle
```

Only four consumers receive work.

---

# Example 5: More Partitions Than Consumers

Topic:

```text
8 Partitions
```

Consumers:

```text
Consumer A

Consumer B
```

Assignments:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3

----------------

Consumer B

↓

Partition 4

Partition 5

Partition 6

Partition 7
```

Each consumer owns multiple partitions.

---

# Example 6: Consumer Joins

Initial state:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

Consumer B starts.

Kafka performs:

```text
Rebalance
```

New assignment:

```text
Consumer A

↓

Partition 0

Partition 1

----------------

Consumer B

↓

Partition 2

Partition 3
```

The workload becomes balanced.

---

# Example 7: Consumer Leaves

Before failure:

```text
Consumer A

↓

Partition 0

Partition 1

----------------

Consumer B

↓

Partition 2

Partition 3
```

Consumer B crashes.

Kafka performs:

```text
Heartbeat Timeout

↓

Rebalance
```

After rebalance:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

Processing continues automatically.

---

# Example 8: Multiple Consumer Groups

Suppose:

```text
Orders Topic
```

Consumer Groups:

```text
Inventory Group

Payment Group

Analytics Group
```

Architecture:

```text
Orders Topic

├── Inventory Group

├── Payment Group

└── Analytics Group
```

Each Consumer Group receives every message independently.

---

# Independent Offsets

Example:

```text
Orders Topic

Latest Offset

1000
```

Inventory Group:

```text
Committed Offset

980
```

Payment Group:

```text
Committed Offset

995
```

Analytics Group:

```text
Committed Offset

1000
```

Each Consumer Group tracks its own progress.

---

# Example 9: Ordering

Partition:

```text
Partition 2

↓

Order Created

↓

Order Paid

↓

Order Packed

↓

Order Delivered
```

One consumer processes:

```text
Created

↓

Paid

↓

Packed

↓

Delivered
```

Ordering is preserved.

---

# Example 10: Scaling Consumers

Current system:

```text
8 Partitions

↓

2 Consumers
```

Processing:

```text
400 Messages/sec
```

Scale:

```text
8 Consumers
```

Now:

```text
800 Messages/sec
```

Parallelism improves throughput.

---

# Example 11: Idle Consumers

Suppose:

```text
3 Partitions

↓

10 Consumers
```

Result:

```text
3 Active

7 Idle
```

Kafka cannot assign multiple consumers to the same partition within one Consumer Group.

---

# Example 12: Consumer Lag

Consumer A:

```text
Partition 0

Lag

5
```

Consumer B:

```text
Partition 1

Lag

350
```

The Consumer Group lag:

```text
355
```

Partition-level monitoring helps identify bottlenecks.

---

# Example 13: Rebalancing

Current assignment:

```text
Consumer A

↓

Partition 0

Partition 1

----------------

Consumer B

↓

Partition 2

Partition 3
```

Consumer C joins.

Kafka performs:

```text
Pause

↓

Reassign

↓

Resume
```

New assignment:

```text
Consumer A → Partition 0

Consumer B → Partition 1

Consumer C → Partition 2

Consumer A → Partition 3
```

Assignments become more balanced.

---

# Example 14: Processing Failure

Workflow:

```text
Poll Message

↓

Process

↓

Crash

↓

Offset Not Committed
```

After restart:

```text
Message Read Again
```

Duplicates may occur.

Applications should use idempotent processing.

---

# Real-World Example

E-commerce platform:

```text
orders.created

↓

Inventory Group

↓

Reserve Stock

----------------

orders.created

↓

Notification Group

↓

Send Email

----------------

orders.created

↓

Analytics Group

↓

Update Dashboard
```

Each Consumer Group processes the same event independently.

---

# Consumer Group Scaling Strategy

```text
More Traffic

↓

Increase Partitions

↓

Increase Consumers

↓

Monitor Lag

↓

Optimize Processing
```

Scaling consumers without increasing partitions provides little benefit.

---

# Best Practices

- Match consumer count to partition count.
- Monitor Consumer Group lag continuously.
- Keep consumer processing efficient.
- Use Manual Offset Commit for critical workloads.
- Avoid unnecessary rebalancing.
- Design consumers to be idempotent.
- Monitor heartbeat failures.
- Scale partitions before adding large numbers of consumers.
- Use multiple Consumer Groups for independent processing.
- Test Consumer Group recovery regularly.

---

# Common Mistakes

- Adding more consumers than partitions.
- Ignoring Consumer Lag.
- Assuming multiple consumers can process one partition simultaneously.
- Restarting all consumers together.
- Ignoring rebalancing events.
- Using Auto Commit for business-critical systems.
- Forgetting that each Consumer Group has independent offsets.
- Designing long-running processing inside the poll loop.

---

# Summary

Consumer Groups enable Kafka to scale message processing while maintaining reliable, ordered consumption within each partition. They automatically distribute partitions among consumers, recover from failures through rebalancing, and allow multiple independent applications to consume the same stream of events. Proper Consumer Group design is essential for building scalable, fault-tolerant, and high-performance Kafka applications.

---

# Key Takeaways

- Consumer Groups enable parallel processing.
- Each partition is assigned to only one consumer within a Consumer Group.
- Multiple Consumer Groups can independently consume the same topic.
- Maximum parallelism equals the number of partitions.
- Rebalancing redistributes partitions when consumers join or leave.
- Consumer Groups maintain independent offsets.
- Consumer Lag is a key health metric.
- Proper Consumer Group design is fundamental to scalable Kafka architectures.