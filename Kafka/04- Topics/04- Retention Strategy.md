# Retention Strategy

## Overview

One of Kafka's most powerful features is that messages are **not deleted immediately after being consumed**.

Unlike traditional message queues where processed messages disappear, Kafka stores messages for a configurable period, allowing multiple consumers to read the same data independently and enabling event replay, auditing, and recovery.

This behavior is controlled through **Retention Policies**.

A retention strategy determines:

- How long messages are stored
- When messages are deleted
- How much storage Kafka requires
- How far consumers can replay historical events

Choosing the correct retention strategy is essential for balancing storage costs, recovery capabilities, and business requirements.

---

# What is Retention?

Retention is the amount of time or storage Kafka keeps messages before deleting them.

Example:

```text
Message Produced

↓

Stored in Kafka

↓

Retention Period

↓

Deleted
```

Messages remain available even after consumers have processed them.

---

# Why Retention Exists

Suppose a consumer crashes.

```text
Consumer

↓

Crash

↓

Restart
```

Kafka can replay old messages because they are still stored.

Without retention:

```text
Message Processed

↓

Deleted

↓

No Recovery
```

Retention enables reliable recovery and replay.

---

# Kafka Log Retention

Kafka stores messages in an append-only log.

```text
Offset

0

↓

1

↓

2

↓

3

↓

4
```

Messages remain in the log until the retention policy removes them.

---

# Retention Workflow

```text
Producer

↓

Kafka Topic

↓

Messages Stored

↓

Retention Policy

↓

Delete Old Data
```

Consumers do not control message deletion.

Kafka manages retention automatically.

---

# Time-Based Retention

The most common strategy is **time-based retention**.

Example:

```properties
retention.ms=604800000
```

Equivalent:

```text
7 Days
```

Messages older than seven days are automatically removed.

---

# Size-Based Retention

Kafka can also delete messages when the log exceeds a configured size.

Example:

```properties
retention.bytes=10737418240
```

Equivalent:

```text
10 GB
```

When the limit is reached:

```text
Oldest Messages

↓

Deleted
```

---

# Combining Time and Size

Kafka supports both policies simultaneously.

Example:

```text
Keep Messages

↓

7 Days

OR

10 GB

↓

Whichever Limit is Reached First
```

This prevents unlimited storage growth.

---

# Message Lifecycle

```text
Produce Message

↓

Store in Partition

↓

Read by Consumers

↓

Retention Period Expires

↓

Delete Message
```

Consumers do not influence this lifecycle.

---

# Consumer Independence

Suppose three Consumer Groups exist.

```text
Orders Topic

↓

Inventory Group

↓

Analytics Group

↓

Audit Group
```

Each group has its own offsets.

Retention is shared by all groups.

If data expires before a consumer reads it:

```text
Message Deleted

↓

Cannot Be Recovered
```

---

# Replay Using Retention

Suppose an analytics service needs to replay last week's data.

```text
Consumer

↓

Seek to Beginning

↓

Replay Messages
```

Replay is only possible while the retained data still exists.

---

# Short Retention

Example:

```text
Retention

↓

1 Hour
```

Advantages:

- Low storage usage
- Fast cleanup

Disadvantages:

- Limited replay capability
- Short recovery window

Suitable for:

- Temporary metrics
- Monitoring data

---

# Long Retention

Example:

```text
Retention

↓

30 Days
```

Advantages:

- Long replay window
- Easier recovery
- Historical analysis

Disadvantages:

- Increased storage requirements

Suitable for:

- Business events
- Audit logs
- Analytics

---

# Unlimited Retention

Kafka can retain data indefinitely.

Example:

```properties
retention.ms=-1
```

Messages remain until deleted manually.

Useful for:

- Compliance
- Event sourcing
- Permanent audit logs

Requires careful storage planning.

---

# Retention and Consumer Lag

Suppose:

```text
Retention

↓

7 Days
```

Consumer:

```text
Offline

↓

10 Days
```

When the consumer restarts:

```text
Messages

Already Deleted
```

Recovery is impossible.

Consumer lag should always remain within the retention window.

---

# Log Segments

Kafka stores data in **log segments**.

```text
Partition

↓

Segment 1

↓

Segment 2

↓

Segment 3
```

Kafka deletes entire segments—not individual messages.

This makes retention efficient.

---

# Segment Deletion

```text
Segment

↓

Retention Expired

↓

Delete Entire Segment
```

Deleting segments is much faster than deleting individual records.

---

# Topic-Level Retention

Retention can be configured for each topic.

Example:

```text
Orders

↓

30 Days

----------------

Metrics

↓

1 Day

----------------

Audit

↓

365 Days
```

Different workloads require different retention policies.

---

# Broker-Level Retention

Kafka also supports default broker-wide retention.

Example:

```properties
log.retention.hours=168
```

Equivalent:

```text
7 Days
```

Topic-specific settings override broker defaults.

---

# Retention vs Compaction

Kafka supports two cleanup strategies.

### Retention

```text
Time

↓

Delete Old Messages
```

---

### Log Compaction

```text
Keep Latest Record

Per Key
```

Retention removes old data based on time or size.

Compaction preserves the latest state for each key.

---

# Storage Planning

Storage depends on:

```text
Messages Per Day

×

Average Message Size

×

Retention Period
```

Example:

```text
10 GB / Day

×

30 Days

=

300 GB
```

Always include replication when estimating storage.

---

# Storage with Replication

Suppose:

```text
10 GB / Day

↓

30 Days

↓

Replication Factor = 3
```

Required storage:

```text
10 × 30 × 3

=

900 GB
```

Replication significantly increases storage requirements.

---

# Retention Strategy Examples

### Metrics

```text
Retention

↓

1 Day
```

Reason:

Historical metrics lose value quickly.

---

### Orders

```text
Retention

↓

30 Days
```

Reason:

Supports recovery and analytics.

---

### Audit Logs

```text
Retention

↓

365 Days
```

Reason:

Compliance and auditing.

---

### Event Sourcing

```text
Retention

↓

Unlimited
```

Reason:

Entire system state can be rebuilt.

---

# Retention Architecture

```text
Producer
      │
      ▼
 Kafka Topic
      │
      ▼
 Append Messages
      │
      ▼
 Log Segments
      │
      ▼
Retention Policy
      │
      ▼
Delete Expired Segments
```

---

# Real-World Example

An e-commerce platform uses different retention periods.

```text
Orders

↓

30 Days

----------------

Payments

↓

90 Days

----------------

Metrics

↓

24 Hours

----------------

Audit Logs

↓

365 Days
```

Each topic is optimized for its business purpose.

---

# Best Practices

- Define retention based on business requirements.
- Keep retention longer than the maximum expected consumer downtime.
- Monitor disk usage regularly.
- Configure retention at the topic level whenever possible.
- Estimate storage before increasing retention periods.
- Consider replay and disaster recovery requirements.
- Remember that replication increases storage consumption.

---

# Common Mistakes

- Assuming messages are deleted after consumption.
- Configuring retention too short for consumer recovery.
- Ignoring storage requirements.
- Using identical retention for every topic.
- Forgetting to include replication in storage calculations.
- Confusing retention with log compaction.

---

# Summary

Retention Strategy determines how long Kafka stores messages before removing them. Kafka supports both time-based and size-based retention, allowing organizations to balance storage costs with replay and recovery capabilities. Because messages remain available after consumption, Kafka enables independent consumers, event replay, and disaster recovery. Choosing an appropriate retention policy requires understanding business requirements, consumer behavior, storage capacity, and replication overhead.

---

# Key Takeaways

- Kafka retains messages independently of consumer progress.
- Retention can be based on time, size, or both.
- Consumers can replay messages while they remain within the retention window.
- Kafka deletes expired log segments rather than individual messages.
- Different topics should have different retention policies based on business needs.
- Retention and log compaction are separate cleanup strategies.
- Storage planning must account for message volume, retention period, and replication.
- A well-designed retention strategy balances operational cost with recovery and replay requirements.