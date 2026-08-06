# Consumer Questions

## Overview

Kafka Consumers are responsible for reading and processing messages from Kafka topics. Since consumers determine how applications process events, interviewers frequently ask questions about Consumer Groups, offsets, polling, commits, rebalancing, lag, partition assignment, and delivery guarantees.

This chapter covers the most commonly asked Kafka Consumer interview questions along with concise, production-oriented answers.

---

# What is a Kafka Consumer?

**Question**

> What is a Kafka Consumer?

**Answer**

A Kafka Consumer is an application that reads messages from one or more Kafka topics.

Example:

```text
Kafka Topic

↓

Inventory Service

↓

Process Event
```

Consumers process events independently of producers.

---

# How Does a Consumer Work?

**Question**

> Explain the Consumer workflow.

**Answer**

Consumer workflow:

```text
Consumer

↓

Subscribe Topic

↓

Poll Messages

↓

Process Records

↓

Commit Offset

↓

Poll Again
```

The consumer continuously polls Kafka for new records.

---

# What is Polling?

**Question**

> What is polling in Kafka?

**Answer**

Kafka consumers actively request new records from brokers using:

```java
consumer.poll(...)
```

Polling allows consumers to fetch available messages.

Consumers do not receive pushed messages.

---

# Why Does Kafka Use Polling Instead of Push?

**Question**

> Why does Kafka use a pull model?

**Answer**

The pull model allows consumers to:

- Control processing speed
- Batch messages efficiently
- Handle backpressure
- Avoid being overwhelmed

Consumers decide when to request more data.

---

# What is a Consumer Group?

**Question**

> What is a Consumer Group?

**Answer**

A Consumer Group is a collection of consumers working together to process a topic.

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

Kafka distributes partitions among consumers in the group.

---

# Can Multiple Consumers Read the Same Message?

**Question**

> Can multiple consumers read the same message?

**Answer**

Yes.

Different Consumer Groups can read the same message independently.

Example:

```text
Orders Topic

↓

Inventory Group

↓

Analytics Group

↓

Notification Group
```

Each group maintains its own offsets.

---

# Can Two Consumers in the Same Group Read the Same Partition?

**Question**

> Can two consumers in the same Consumer Group consume the same partition simultaneously?

**Answer**

No.

Within a Consumer Group:

```text
1 Partition

↓

1 Consumer
```

This prevents duplicate processing.

---

# What is an Offset?

**Question**

> What is an Offset?

**Answer**

An Offset is the position of a record within a partition.

Example:

```text
Offset 100

↓

Offset 101

↓

Offset 102
```

Consumers use offsets to track processing progress.

---

# Why Are Offsets Important?

**Question**

> Why does Kafka use offsets?

**Answer**

Offsets allow consumers to:

- Resume after failures
- Replay messages
- Track progress independently
- Process data reliably

Each Consumer Group stores its own offsets.

---

# What is Auto Commit?

**Question**

> What is Auto Commit?

**Answer**

With Auto Commit enabled:

```properties
enable.auto.commit=true
```

Kafka periodically commits offsets automatically.

Advantages:

- Simple configuration

Disadvantages:

- Increased risk of message loss if processing fails after commit.

---

# What is Manual Commit?

**Question**

> Why use Manual Offset Commit?

**Answer**

Manual commit allows applications to commit offsets only after successful processing.

Workflow:

```text
Receive Message

↓

Process Successfully

↓

Commit Offset
```

This provides greater control and reliability.

---

# Which Offset Commit Strategy Is Better?

**Question**

> Auto Commit or Manual Commit?

**Answer**

For production systems:

Manual Commit is generally preferred because it reduces the risk of data loss.

Auto Commit is suitable for simpler applications where occasional duplicates or losses are acceptable.

---

# What is Consumer Lag?

**Question**

> What is Consumer Lag?

**Answer**

Consumer Lag is:

```text
Latest Offset

-

Committed Offset
```

Large lag indicates consumers are processing messages more slowly than producers are publishing them.

---

# What Causes Consumer Lag?

**Question**

> Why does Consumer Lag increase?

**Answer**

Common causes:

- Slow business logic
- Database bottlenecks
- External API calls
- Too few consumers
- Too few partitions
- Frequent rebalancing
- Slow brokers

---

# What is Rebalancing?

**Question**

> What is Consumer Group Rebalancing?

**Answer**

Rebalancing redistributes partitions among consumers whenever group membership changes.

Triggers include:

- Consumer joins
- Consumer leaves
- Consumer crash
- Partition count changes

---

# Why Are Frequent Rebalances Bad?

**Question**

> Why should excessive rebalancing be avoided?

**Answer**

During a rebalance:

```text
Consumers Pause

↓

Partitions Reassigned

↓

Consumers Resume
```

Effects:

- Temporary pause in processing
- Increased consumer lag
- Reduced throughput

---

# What Happens If a Consumer Crashes?

**Question**

> What happens when a consumer fails?

**Answer**

Kafka detects the missing consumer through heartbeat timeouts.

Workflow:

```text
Consumer Crash

↓

Heartbeat Timeout

↓

Rebalance

↓

Partitions Assigned

↓

Processing Continues
```

Remaining consumers continue processing.

---

# What is `auto.offset.reset`?

**Question**

> What does `auto.offset.reset` do?

**Answer**

It determines where a consumer starts reading if no committed offset exists.

Options:

```properties
earliest
```

Read from the beginning.

---

```properties
latest
```

Read only new messages.

---

# What Happens If Offsets Are Lost?

**Question**

> What happens if committed offsets disappear?

**Answer**

Kafka applies:

```properties
auto.offset.reset
```

to determine the starting point.

Depending on configuration, consumers may replay old messages or skip historical data.

---

# What is `max.poll.interval.ms`?

**Question**

> Why is `max.poll.interval.ms` important?

**Answer**

It specifies the maximum time allowed between successive `poll()` calls.

If exceeded:

```text
Consumer Removed

↓

Rebalance
```

Long-running processing should be considered when configuring this value.

---

# What Are Heartbeats?

**Question**

> Why do consumers send heartbeats?

**Answer**

Heartbeats inform the Group Coordinator that the consumer is still alive.

Workflow:

```text
Consumer

↓

Heartbeat

↓

Coordinator
```

Missing heartbeats eventually trigger rebalancing.

---

# Consumer Best Practices

**Question**

> What are Kafka Consumer best practices?

**Answer**

- Commit offsets after successful processing.
- Monitor Consumer Lag.
- Keep processing efficient.
- Batch expensive operations.
- Handle duplicate messages safely.
- Use idempotent business logic.
- Configure polling and heartbeat settings appropriately.
- Avoid unnecessary rebalancing.
- Monitor Consumer Group health.
- Test failure recovery scenarios.

---

# Scenario-Based Questions

### Question

> Consumer Lag suddenly increases. What would you investigate?

**Answer**

Check:

- Consumer health
- Database performance
- External APIs
- Consumer processing time
- Broker health
- Network latency
- Partition count

---

### Question

> Why are duplicate messages appearing?

**Answer**

Possible causes:

- Consumer restarted before committing offsets
- Manual offset reset
- At-least-once delivery semantics

Consumers should be designed to be idempotent.

---

### Question

> Why are some consumers idle?

**Answer**

If:

```text
Consumers

>

Partitions
```

Extra consumers remain idle because only one consumer in a Consumer Group can process a partition.

---

### Question

> Why would you choose Manual Commit over Auto Commit?

**Answer**

Manual Commit allows offsets to be committed only after successful processing, reducing the risk of losing messages during application failures.

---

### Question

> What happens if processing takes longer than `max.poll.interval.ms`?

**Answer**

Kafka assumes the consumer has failed.

Result:

```text
Consumer Removed

↓

Rebalance
```

Applications should optimize processing or adjust the configuration appropriately.

---

# Frequently Asked Interview Questions

- What is a Kafka Consumer?
- How does polling work?
- Why does Kafka use polling?
- What is a Consumer Group?
- What is Consumer Lag?
- What causes Consumer Lag?
- What is an Offset?
- What is Auto Commit?
- What is Manual Commit?
- What is Rebalancing?
- Why are heartbeats important?
- What is `auto.offset.reset`?
- What is `max.poll.interval.ms`?
- Why are some consumers idle?
- What are Kafka Consumer best practices?

---

# Summary

Kafka Consumers are responsible for reading, processing, and acknowledging messages stored in Kafka topics. Interview questions typically focus on polling, Consumer Groups, offsets, lag, commits, and rebalancing because these concepts directly influence reliability and scalability. A strong understanding of consumer behavior and offset management demonstrates the ability to build robust, production-ready event processing systems.

---

# Key Takeaways

- Consumers read records by continuously polling Kafka.
- Consumer Groups enable scalable parallel processing.
- Offsets track processing progress independently for each Consumer Group.
- Manual offset commits provide greater reliability than automatic commits.
- Consumer Lag is a critical production metric.
- Rebalancing redistributes partitions when Consumer Group membership changes.
- Heartbeats help Kafka detect failed consumers.
- Proper consumer configuration and monitoring are essential for reliable Kafka applications.