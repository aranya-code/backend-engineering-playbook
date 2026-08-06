# Retention Policies

## Overview

One of Apache Kafka's most powerful features is that it **does not immediately delete messages after they are consumed**. Instead, Kafka retains messages for a configurable period or until certain storage limits are reached.

This behavior allows applications to:

- Replay historical events
- Recover from failures
- Build new consumers without affecting existing ones
- Perform auditing and analytics
- Reprocess old data

Kafka manages message retention using **Retention Policies**, which determine **how long** messages should remain in the cluster before they are deleted.

Unlike traditional message queues, Kafka treats consumed messages and stored messages as independent concepts.

---

# What is Message Retention?

Message retention is the process of deciding **how long Kafka keeps messages**.

Example:

```text
Producer

↓

Kafka

↓

Consumer

↓

Message Still Exists
```

Even after the consumer reads the message, Kafka continues storing it until the configured retention policy expires.

---

# Why Doesn't Kafka Delete Messages Immediately?

Traditional queues behave like this:

```text
Producer

↓

Queue

↓

Consumer

↓

Delete Message
```

Kafka behaves differently.

```text
Producer

↓

Kafka

↓

Consumer

↓

Message Remains
```

This enables:

- Event replay
- Multiple consumers
- Fault recovery
- Historical analysis

---

# How Retention Works

Kafka continuously stores new messages.

```text
Offset 0

Offset 1

Offset 2

Offset 3

Offset 4

Offset 5
```

As messages become older than the configured retention period, Kafka removes them.

Example:

```text
Today

↓

Offset 100

↓

7 Days Later

↓

Deleted
```

---

# Time-Based Retention

The most common retention policy is based on time.

Example:

```properties
log.retention.hours=168
```

Equivalent to:

```text
7 Days
```

Messages older than seven days become eligible for deletion.

Example:

```text
Day 1

Keep

---------------

Day 4

Keep

---------------

Day 8

Delete
```

---

# Size-Based Retention

Kafka can also retain messages based on total log size.

Example:

```properties
log.retention.bytes=10737418240
```

Equivalent to:

```text
10 GB
```

When the log exceeds 10 GB:

```text
11 GB

↓

Delete Oldest Segments

↓

10 GB
```

Kafka removes the oldest segments first.

---

# Time and Size Together

Kafka evaluates both conditions.

Suppose:

```text
Retention

7 Days

Maximum Size

20 GB
```

A segment is deleted when either condition is met.

```text
Old Segment

↓

Older than 7 Days

↓

Delete
```

or

```text
Storage > 20 GB

↓

Delete Oldest Segment
```

---

# Segment-Based Deletion

Kafka does **not** delete individual messages.

Instead:

```text
Partition

↓

Segment 1

↓

Segment 2

↓

Segment 3
```

Suppose Segment 1 exceeds the retention period.

```text
Segment 1

↓

Delete Entire Segment
```

This makes cleanup extremely efficient.

---

# Example Timeline

Suppose retention is seven days.

```text
Day 1

Order A

----------------

Day 2

Order B

----------------

Day 3

Order C

----------------

Day 8

Order A Deleted

----------------

Day 9

Order B Deleted
```

Kafka continuously removes old segments.

---

# Retention and Consumers

Consumers do **not** influence retention.

Example:

```text
Consumer Never Reads Message

↓

Retention Expires

↓

Message Deleted
```

Similarly,

```text
Consumer Already Read Message

↓

Retention Not Expired

↓

Message Still Exists
```

Retention is controlled entirely by Kafka broker configuration.

---

# Event Replay

Retention enables replay.

Example:

```text
Offset 0

↓

Offset 5000
```

A new consumer joins.

```text
auto.offset.reset=earliest
```

Kafka allows the consumer to process historical messages that still exist within the retention window.

---

# Long Retention Example

Suppose:

```text
Retention

30 Days
```

Benefits:

- Easier debugging
- Historical analytics
- Disaster recovery
- Consumer replay

Trade-off:

- More disk storage

---

# Short Retention Example

Suppose:

```text
Retention

24 Hours
```

Benefits:

- Lower storage costs
- Faster cleanup

Trade-off:

- Less historical data
- Limited replay capability

---

# Unlimited Retention

Kafka can be configured to retain messages indefinitely.

Example:

```properties
log.retention.ms=-1
```

Messages remain until:

- Manual deletion
- Topic deletion
- Storage exhaustion

This configuration is uncommon because storage requirements continue growing.

---

# Retention and Log Compaction

Retention and log compaction are different cleanup strategies.

Retention:

```text
Old Data

↓

Delete Entire Segment
```

Log Compaction:

```text
Duplicate Keys

↓

Keep Latest Record

↓

Remove Older Versions
```

Both policies can be configured independently depending on the use case.

---

# Topic-Level Retention

Retention settings can be configured per topic.

Example:

```text
orders

Retention = 30 Days

-----------------------

logs

Retention = 7 Days

-----------------------

metrics

Retention = 24 Hours
```

This allows each topic to have its own lifecycle.

---

# Common Retention Strategies

| Topic | Typical Retention |
|---------|------------------|
| Logs | 7 Days |
| Metrics | 24 Hours |
| Orders | 30 Days |
| Payments | 90 Days |
| Audit Logs | 1 Year |
| Analytics | 30–180 Days |

Actual values depend on business and compliance requirements.

---

# Advantages of Retention

- Supports event replay
- Enables auditing
- Improves disaster recovery
- Allows multiple consumers
- Simplifies debugging
- Enables historical analytics

---

# Limitations

- Requires disk storage
- Longer retention increases storage costs
- Very short retention limits replay capability
- Poor retention planning can impact cluster capacity

---

# Best Practices

- Configure retention based on business requirements.
- Use topic-specific retention policies.
- Monitor disk utilization regularly.
- Balance replay needs with storage costs.
- Use longer retention for audit and financial topics.
- Periodically review retention settings as workloads evolve.

---

# Common Mistakes

- Assuming messages are deleted immediately after consumption.
- Confusing retention with consumer offsets.
- Configuring extremely long retention without sufficient storage.
- Using the same retention period for every topic.
- Ignoring compliance or legal data retention requirements.

---

# Summary

Kafka retention policies determine how long messages remain stored in the cluster. Messages are retained independently of consumer activity and are removed only when configured time or size limits are exceeded. Kafka deletes entire log segments rather than individual messages, making retention highly efficient. Proper retention planning allows organizations to balance storage costs, replay capability, compliance requirements, and operational flexibility.

---

# Key Takeaways

- Kafka retains messages even after they are consumed.
- Retention can be configured using time, size, or both.
- Kafka deletes entire log segments, not individual messages.
- Consumer activity does not affect message retention.
- Longer retention enables replay, auditing, and recovery.
- Shorter retention reduces storage requirements.
- Retention policies can be configured per topic.
- Proper retention planning is essential for balancing storage costs and business requirements.