# Partition Assignment

## Overview

When multiple consumers belong to the same Consumer Group, Kafka must decide **which consumer should read which partition**.

This process is called **Partition Assignment**.

Partition Assignment ensures that:

- Every partition is processed by only one consumer within a group.
- The workload is distributed as evenly as possible.
- Consumers can scale horizontally.
- Failures can be handled automatically.

Partition Assignment is one of the core mechanisms behind Kafka's scalability and fault tolerance.

---

# What is Partition Assignment?

Partition Assignment is the process of mapping topic partitions to consumers within a Consumer Group.

Example:

```text
Orders Topic

Partition 0

Partition 1

Partition 2

Partition 3
```

Consumer Group:

```text
Consumer A

Consumer B
```

Kafka assigns:

```text
Consumer A

↓

Partition 0

Partition 2

-------------------

Consumer B

↓

Partition 1

Partition 3
```

---

# Why Partition Assignment is Needed

Suppose a topic has:

```text
8 Partitions
```

and four consumers.

Without assignment:

```text
Every Consumer

↓

Reads Everything
```

Problems:

- Duplicate processing
- Wasted resources
- Poor scalability

With assignment:

```text
Partition

↓

One Consumer
```

Kafka distributes the workload efficiently.

---

# Assignment Workflow

```text
Consumer Starts

↓

Join Consumer Group

↓

Group Coordinator

↓

Assignment Strategy

↓

Partitions Assigned

↓

Consumer Starts Polling
```

---

# Group Coordinator

Partition assignment is managed by the **Group Coordinator**.

Responsibilities:

- Register consumers
- Detect membership changes
- Execute assignment strategy
- Notify consumers
- Trigger rebalancing when needed

Architecture:

```text
Consumers

↓

Group Coordinator

↓

Assignment Strategy

↓

Partition Assignment
```

---

# Assignment Goals

Kafka attempts to:

- Balance partitions evenly.
- Minimize partition movement.
- Preserve processing order.
- Reduce rebalancing time.

A good assignment improves throughput and reduces consumer downtime.

---

# Example Assignment

Suppose:

```text
Topic

6 Partitions
```

Consumers:

```text
Consumer A

Consumer B

Consumer C
```

Assignment:

```text
Consumer A

↓

P0

P3

----------------

Consumer B

↓

P1

P4

----------------

Consumer C

↓

P2

P5
```

Each consumer processes two partitions.

---

# Uneven Assignment

Suppose:

```text
Topic

7 Partitions

Consumers

3
```

Kafka cannot divide partitions perfectly.

Assignment:

```text
Consumer A

↓

P0

P3

P6

----------------

Consumer B

↓

P1

P4

----------------

Consumer C

↓

P2

P5
```

Kafka distributes partitions as evenly as possible.

---

# More Consumers Than Partitions

Suppose:

```text
Topic

3 Partitions

Consumers

5
```

Assignment:

```text
Consumer A

↓

P0

----------------

Consumer B

↓

P1

----------------

Consumer C

↓

P2

----------------

Consumer D

Idle

----------------

Consumer E

Idle
```

Extra consumers remain idle.

Kafka cannot split a partition.

---

# More Partitions Than Consumers

Suppose:

```text
Topic

12 Partitions

Consumers

3
```

Assignment:

```text
Consumer A

↓

4 Partitions

----------------

Consumer B

↓

4 Partitions

----------------

Consumer C

↓

4 Partitions
```

Increasing partitions enables greater parallelism.

---

# Assignment Strategies

Kafka supports multiple partition assignment strategies.

The most common are:

- Range Assignor
- Round Robin Assignor
- Sticky Assignor
- Cooperative Sticky Assignor

Each strategy has different goals and trade-offs.

---

# Range Assignor

The **Range Assignor** assigns consecutive partitions.

Example:

```text
Topic

P0

P1

P2

P3

P4

P5
```

Consumers:

```text
A

B
```

Assignment:

```text
Consumer A

↓

P0

P1

P2

----------------

Consumer B

↓

P3

P4

P5
```

Advantages:

- Simple
- Predictable

Limitations:

- May become unbalanced across multiple topics.

---

# Round Robin Assignor

Partitions are assigned one by one.

Example:

```text
Consumer A

↓

P0

P2

P4

----------------

Consumer B

↓

P1

P3

P5
```

Advantages:

- Excellent load balancing

Limitations:

- May move many partitions during rebalancing.

---

# Sticky Assignor

The Sticky Assignor tries to:

- Keep existing assignments
- Balance workload
- Reduce partition movement

Example:

Before:

```text
Consumer A

↓

P0

P1

----------------

Consumer B

↓

P2

P3
```

After a rebalance:

```text
Consumer A

↓

P0

P1

P2

----------------

Consumer B

↓

P3
```

Kafka moves only the partitions necessary.

---

# Cooperative Sticky Assignor

The Cooperative Sticky Assignor improves further.

Instead of revoking every partition:

```text
Move

Only

Required Partitions
```

Advantages:

- Smaller pauses
- Faster recovery
- Lower consumer downtime

This is the recommended strategy for modern Kafka deployments.

---

# Assignment During Rebalancing

Suppose a consumer joins.

Before:

```text
Consumer A

↓

P0

P1

P2

P3
```

After:

```text
Consumer A

↓

P0

P1

----------------

Consumer B

↓

P2

P3
```

Kafka performs a new assignment automatically.

---

# Assignment and Offsets

Partition ownership changes, but offsets remain.

Example:

```text
Consumer A

↓

P0

Committed Offset

250
```

After reassignment:

```text
Consumer B

↓

P0

Starts From

251
```

Kafka resumes from the committed offset.

---

# Assignment and Ordering

Kafka guarantees ordering within a partition.

Suppose:

```text
Partition

Message A

↓

Message B

↓

Message C
```

Even if the partition moves to another consumer:

```text
Consumer B

↓

Message D
```

Ordering is preserved.

---

# Static Membership

Static Membership reduces unnecessary partition movement.

Configuration:

```properties
group.instance.id=consumer-1
```

Benefits:

- Stable assignments
- Fewer rebalances
- Less partition movement

Useful for long-running production services.

---

# Assignment Configuration

Kafka allows selecting the assignment strategy.

Example:

```properties
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
```

Multiple assignors may also be configured in order of preference.

---

# Assignment Architecture

```text
                  Kafka Cluster
                        │
                        ▼
               Group Coordinator
                        │
                        ▼
            Assignment Strategy
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Consumer A      Consumer B      Consumer C
        │               │               │
      P0,P3           P1,P4           P2,P5
```

---

# Real-World Example

An e-commerce application has:

```text
Orders Topic

12 Partitions
```

Consumer Group:

```text
Order Worker 1

Order Worker 2

Order Worker 3

Order Worker 4
```

Kafka automatically distributes the partitions.

If another worker starts:

```text
Order Worker 5
```

Kafka performs a rebalance and redistributes the partitions.

---

# Advantages

- Automatic load balancing.
- Horizontal scalability.
- Fault tolerance.
- Parallel processing.
- Automatic recovery.
- Even workload distribution.

---

# Limitations

- Rebalancing temporarily pauses consumers.
- Some assignment strategies move many partitions.
- Maximum parallelism is limited by the number of partitions.

---

# Best Practices

- Create enough partitions for future scaling.
- Prefer the Cooperative Sticky Assignor for modern deployments.
- Monitor rebalance frequency.
- Use Static Membership for stable long-running consumers.
- Commit offsets before partition revocation.
- Design consumers to tolerate partition movement.

---

# Common Mistakes

- Creating more consumers than partitions expecting higher throughput.
- Assuming partitions are permanently assigned.
- Ignoring the impact of assignment strategy on performance.
- Using the default strategy without understanding its trade-offs.
- Forgetting that partition ownership changes during rebalancing.

---

# Summary

Partition Assignment is the mechanism Kafka uses to distribute topic partitions among consumers within a Consumer Group. Managed by the Group Coordinator, the assignment process balances workload, enables parallel processing, and supports automatic recovery during failures. Kafka provides multiple assignment strategies—including Range, Round Robin, Sticky, and Cooperative Sticky Assignors—each offering different trade-offs between load balancing and partition stability. Choosing the appropriate strategy is essential for building scalable and efficient Kafka consumer applications.

---

# Key Takeaways

- Partition Assignment maps partitions to consumers within a Consumer Group.
- Each partition is assigned to only one consumer in a group.
- The Group Coordinator manages partition assignments.
- Kafka supports Range, Round Robin, Sticky, and Cooperative Sticky assignment strategies.
- Cooperative Sticky Assignor minimizes partition movement and reduces downtime.
- Offsets move with partitions, allowing consumers to resume correctly after reassignment.
- Partition Assignment enables horizontal scaling and fault tolerance.
- The number of partitions determines the maximum parallelism achievable by a Consumer Group.