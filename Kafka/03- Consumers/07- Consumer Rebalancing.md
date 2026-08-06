# Consumer Rebalancing

## Overview

One of Kafka's most powerful features is its ability to automatically redistribute work when consumers join, leave, or fail.

This automatic redistribution is called **Consumer Rebalancing**.

Rebalancing allows Kafka to:

- Scale consumers horizontally
- Recover from failures
- Balance workload evenly
- Maintain fault tolerance

Although rebalancing is essential for scalability, it temporarily pauses message consumption. Understanding when and why rebalancing occurs is critical for building efficient Kafka consumer applications.

---

# What is Consumer Rebalancing?

Consumer Rebalancing is the process of redistributing partitions among consumers in a consumer group.

Example:

Before:

```text
Consumer Group

Consumer A

↓

Partition 0

Partition 1

--------------------

Consumer B

↓

Partition 2

Partition 3
```

After Consumer C joins:

```text
Consumer A

↓

Partition 0

--------------------

Consumer B

↓

Partition 1

--------------------

Consumer C

↓

Partition 2

Partition 3
```

Kafka automatically balances the workload.

---

# Why Rebalancing is Needed

Suppose an application has one consumer.

```text
Orders Topic

↓

Consumer A
```

Traffic increases.

A second consumer starts.

```text
Consumer A

Consumer B
```

Kafka must redistribute partitions.

Without rebalancing:

```text
Consumer A

↓

Everything
```

With rebalancing:

```text
Consumer A

↓

Half

------------------

Consumer B

↓

Half
```

Workload becomes evenly distributed.

---

# Rebalancing Workflow

```text
Consumer Group Change

↓

Pause Consumption

↓

Group Coordinator

↓

Assign Partitions

↓

Commit Assignments

↓

Resume Consumption
```

This process is automatic.

---

# Group Coordinator

Every consumer group has a **Group Coordinator**.

Responsibilities:

- Detect consumer changes
- Start rebalancing
- Assign partitions
- Track group membership

Architecture:

```text
Consumers

↓

Group Coordinator

↓

Kafka Cluster
```

---

# When Does Rebalancing Occur?

Kafka triggers rebalancing when:

- A new consumer joins.
- A consumer leaves gracefully.
- A consumer crashes.
- A consumer stops sending heartbeats.
- Topic partitions increase.
- Consumer subscriptions change.

Any membership change requires partition redistribution.

---

# Consumer Joins

Before:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

New consumer joins.

After:

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

---

# Consumer Leaves

Before:

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

Consumer B exits.

After:

```text
Consumer A

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

Remaining consumers take ownership.

---

# Consumer Crash

Suppose:

```text
Consumer B

↓

Crash
```

Heartbeats stop.

```text
Heartbeat Timeout

↓

Group Coordinator

↓

Rebalance
```

Partitions are reassigned automatically.

---

# Partition Increase

Suppose:

```text
Orders Topic

4 Partitions
```

Later:

```text
Orders Topic

8 Partitions
```

Kafka triggers rebalancing so consumers can process the new partitions.

---

# Subscription Change

Suppose:

```text
Consumer

↓

Orders Topic
```

Application changes to:

```text
Orders

Payments
```

Kafka performs another rebalance.

---

# Rebalance Lifecycle

Every rebalance follows these stages.

```text
Detect Change

↓

Stop Fetching

↓

Revoke Partitions

↓

Assign Partitions

↓

Resume Polling
```

---

# Partition Revocation

Before new assignments:

```text
Consumer A

↓

Release Partition 1
```

The partition becomes temporarily unassigned.

---

# Partition Assignment

After revocation:

```text
Coordinator

↓

Assign Partition

↓

Consumer B
```

The new consumer begins reading from the last committed offset.

---

# Consumption Pause

During rebalancing:

```text
Consumers

↓

Paused
```

No records are processed.

Once assignments complete:

```text
Resume Polling
```

This temporary pause is normal.

---

# Offset During Rebalancing

Suppose:

```text
Consumer A

↓

Committed Offset

250
```

After reassignment:

```text
Consumer B

↓

Starts

251
```

Committed offsets prevent message loss.

---

# Heartbeats

Consumers periodically send:

```text
Heartbeat

↓

Coordinator
```

Example:

```text
Heartbeat

↓

Alive
```

No heartbeat:

```text
Heartbeat Timeout

↓

Rebalance
```

---

# Session Timeout

Kafka waits for heartbeats.

Configuration:

```properties
session.timeout.ms=45000
```

Equivalent:

```text
45 Seconds
```

If no heartbeat arrives before the timeout:

```text
Consumer Removed
```

---

# Rebalance Timeout

Kafka also limits how long consumers may take during rebalancing.

Configuration:

```properties
max.poll.interval.ms
```

If exceeded:

```text
Consumer Removed

↓

Rebalance
```

Long-running processing frequently causes this problem.

---

# Eager Rebalancing

Older Kafka versions use **Eager Rebalancing**.

Workflow:

```text
Stop Everyone

↓

Revoke All Partitions

↓

Assign Again

↓

Resume
```

Disadvantages:

- Longer pauses
- Lower throughput

---

# Cooperative Rebalancing

Modern Kafka supports **Cooperative Rebalancing**.

Workflow:

```text
Move Only Necessary Partitions

↓

Continue Processing

↓

Minimal Pause
```

Advantages:

- Smaller interruptions
- Faster recovery
- Better performance

---

# Rebalancing Example

Suppose:

```text
Topic

6 Partitions

Consumers

2
```

Assignment:

```text
Consumer A

P0

P1

P2

-----------------

Consumer B

P3

P4

P5
```

New consumer joins.

After rebalance:

```text
Consumer A

P0

P1

----------------

Consumer B

P2

P3

----------------

Consumer C

P4

P5
```

Load becomes balanced.

---

# Rebalancing Architecture

```text
Consumer Group

↓

Membership Change

↓

Group Coordinator

↓

Revoke Partitions

↓

Assign Partitions

↓

Resume Poll Loop
```

---

# Performance Impact

Frequent rebalancing causes:

- Consumption pauses
- Increased latency
- Lower throughput
- Additional network traffic

Applications should minimize unnecessary rebalances.

---

# How to Reduce Rebalancing

Recommendations:

- Keep consumers alive.
- Poll regularly.
- Avoid long processing inside the poll loop.
- Shut down consumers gracefully.
- Use Cooperative Rebalancing.
- Use Static Membership where appropriate.

These techniques improve consumer stability.

---

# Advantages

- Automatic recovery
- Dynamic scaling
- Load balancing
- High availability
- Fault tolerance

---

# Limitations

- Temporary pause in processing
- Increased latency
- More coordination overhead
- Potential duplicate processing after failures

---

# Best Practices

- Commit offsets before partitions are revoked.
- Keep polling regularly.
- Avoid blocking the poll loop.
- Monitor rebalance frequency.
- Prefer Cooperative Rebalancing for modern deployments.
- Use graceful shutdowns to reduce unnecessary rebalances.
- Monitor heartbeat failures.

---

# Common Mistakes

- Assuming rebalancing is instantaneous.
- Ignoring heartbeat timeouts.
- Performing lengthy business logic inside the polling thread.
- Not committing offsets before partition revocation.
- Treating frequent rebalances as normal production behavior.

---

# Summary

Consumer Rebalancing is Kafka's mechanism for redistributing partitions whenever consumer group membership changes. The Group Coordinator manages this process by detecting joins, leaves, crashes, and other membership changes, then assigning partitions to maintain balanced workloads. Although rebalancing temporarily pauses message consumption, it enables Kafka to provide scalability, fault tolerance, and automatic recovery. Modern Kafka deployments reduce disruption through Cooperative Rebalancing and careful consumer design.

---

# Key Takeaways

- Consumer Rebalancing redistributes partitions among consumers.
- The Group Coordinator manages every rebalance.
- Rebalancing occurs when consumers join, leave, crash, or when partition assignments change.
- Consumption pauses briefly during rebalancing.
- Heartbeats are used to detect failed consumers.
- Committed offsets allow new consumers to resume processing correctly.
- Cooperative Rebalancing minimizes interruptions compared to Eager Rebalancing.
- Well-designed consumers reduce unnecessary rebalances and improve overall system stability.