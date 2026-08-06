# Offset Problems

## Overview

Offsets are the foundation of Kafka's consumer model. Every message stored in a partition receives a unique offset, allowing consumers to track their progress independently. Unlike traditional message queues, Kafka does not track which messages have been consumed. Instead, consumers are responsible for committing offsets that indicate how much data has been processed.

Incorrect offset management can lead to:

- Duplicate message processing
- Message loss
- Consumer lag
- Infinite message reprocessing
- Failed recovery after restart

Understanding common offset-related issues is essential for building reliable Kafka consumers.

---

# What is an Offset?

An offset is a sequential number assigned to every record within a partition.

Example:

```text
Partition 0

Offset 0

↓

Offset 1

↓

Offset 2

↓

Offset 3
```

Offsets increase continuously.

---

# Offset Lifecycle

```text
Producer

↓

Message Written

↓

Offset Assigned

↓

Consumer Reads

↓

Offset Committed
```

The committed offset represents consumer progress.

---

# Common Offset Problems

Production systems commonly encounter:

- Offset not committed
- Duplicate processing
- Message loss
- Offset reset
- Invalid offset
- Offset out of range
- Wrong commit timing
- Corrupted consumer state

---

# Offset Not Committed

### Symptoms

Consumer restarts.

```text
Consumer Restart

↓

Reads Same Messages Again
```

Messages are processed multiple times.

---

### Cause

Offsets were never committed.

---

### Solution

Ensure offsets are committed after successful processing.

---

# Auto Commit Too Early

Example:

```text
Receive Message

↓

Auto Commit

↓

Application Crash
```

Result:

```text
Message Lost
```

Kafka believes the message has already been processed.

---

### Solution

Use manual commits for critical applications.

Commit only after successful processing.

---

# Manual Commit Too Late

Example:

```text
Receive Message

↓

Process Message

↓

Crash

↓

No Commit
```

After restart:

```text
Same Message

↓

Processed Again
```

Duplicates occur.

---

### Solution

Design consumers to be idempotent.

---

# Duplicate Processing

### Symptoms

```text
Order Created

↓

Processed Twice
```

Common causes:

- Consumer crash
- Commit failure
- Network interruption

---

### Solution

Use:

- Idempotent business logic
- Deduplication
- Transactional processing

---

# Message Loss

Example:

```text
Receive Message

↓

Commit Offset

↓

Application Crash
```

Processing never completed.

After restart:

```text
Consumer Starts

↓

Skips Message
```

The message is permanently lost.

---

### Solution

Never commit offsets before successful processing.

---

# Offset Out of Range

### Symptoms

Consumer error:

```text
OffsetOutOfRangeException
```

---

### Causes

- Offset deleted
- Retention expired
- Log truncated

---

### Solution

Configure:

```properties
auto.offset.reset=earliest
```

or

```properties
auto.offset.reset=latest
```

depending on business requirements.

---

# Retention Expired

Suppose:

```text
Consumer Offline

↓

7 Days

↓

Retention Deletes Data

↓

Consumer Returns
```

The stored offset no longer exists.

---

### Solution

Increase retention or reduce consumer downtime.

---

# Wrong Offset Reset Policy

Example:

```properties
auto.offset.reset=latest
```

Consumer starts:

```text
Old Messages

↓

Skipped
```

If historical processing is required, use:

```properties
auto.offset.reset=earliest
```

---

# Consumer Group Deleted

Suppose:

```text
Consumer Group Removed
```

Committed offsets disappear.

Next startup:

```text
Offset Reset Policy Applied
```

Consumers may start from the beginning or the end depending on configuration.

---

# Offset Commit Failure

### Symptoms

```text
Commit Failed
```

Possible causes:

- Broker unavailable
- Network failure
- Consumer removed from group

---

### Solution

Retry commit and investigate broker health.

---

# Long Processing Time

Suppose:

```text
Receive

↓

Long Processing

↓

Heartbeat Lost

↓

Rebalance

↓

Commit Fails
```

The consumer loses ownership of its partitions before committing.

---

### Solution

Adjust:

```properties
max.poll.interval.ms
```

and optimize processing time.

---

# Manual Seek Errors

Consumers may reposition offsets using:

```java
consumer.seek(...)
```

Incorrect usage can result in:

```text
Skip Messages

OR

Reprocess Messages
```

Seek should only be used intentionally.

---

# Offset Storage

Committed offsets are stored in:

```text
__consumer_offsets
```

If this internal topic becomes unavailable, consumers cannot commit progress.

---

# Monitoring Offset Health

Monitor:

- Consumer lag
- Commit failures
- Offset commit latency
- Rebalance frequency
- Consumer Group status

These metrics help detect offset issues early.

---

# Viewing Offsets

Display Consumer Group offsets:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--describe \
--group inventory-group
```

Example:

```text
TOPIC       PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG
orders      0         980            1000           20
orders      1         450            452            2
```

---

# Resetting Offsets

Kafka provides:

```bash
kafka-consumer-groups.sh \
--bootstrap-server localhost:9092 \
--group inventory-group \
--reset-offsets
```

Offsets can be reset to:

- Earliest
- Latest
- Specific offset
- Timestamp

Use with caution in production.

---

# Troubleshooting Workflow

```text
Offset Problem

↓

Check Consumer Logs

↓

Check Consumer Group

↓

Check Lag

↓

Check Commit Status

↓

Check Retention

↓

Identify Root Cause

↓

Fix

↓

Validate
```

---

# Quick Diagnosis Table

| Problem | Possible Cause | Recommended Action |
|----------|----------------|--------------------|
| Duplicate Messages | Commit failed | Use idempotent processing |
| Message Loss | Commit before processing | Commit after success |
| Offset Out of Range | Retention expired | Reset offsets |
| Commit Failure | Broker/network issue | Check cluster health |
| Large Lag | Consumer behind | Investigate processing bottleneck |
| Consumer Restart Reads Old Messages | Offsets not committed | Verify commit logic |

---

# Best Practices

- Commit offsets only after successful processing.
- Prefer manual commits for business-critical applications.
- Design consumers to be idempotent.
- Monitor commit failures.
- Monitor Consumer Group lag.
- Configure `auto.offset.reset` appropriately.
- Keep consumers running to avoid retention-related issues.
- Test offset recovery scenarios before production deployment.
- Understand the implications of resetting offsets.
- Document offset management strategies for each application.

---

# Common Mistakes

- Committing offsets before processing.
- Ignoring commit failures.
- Using `auto.offset.reset=latest` without understanding its impact.
- Resetting production offsets accidentally.
- Assuming offsets are globally unique.
- Ignoring Consumer Group state.
- Not testing consumer restart scenarios.
- Relying solely on auto-commit for critical workloads.

---

# Summary

Offsets allow Kafka consumers to track processing progress independently and recover from failures. Improper offset management can lead to duplicate processing, message loss, or replay of historical events. By committing offsets at the correct time, monitoring Consumer Groups, configuring reset policies carefully, and designing idempotent consumers, engineers can build reliable Kafka applications that recover safely from failures while maintaining consistent message processing.

---

# Key Takeaways

- Offsets represent a consumer's progress within a partition.
- Commit offsets only after successful message processing.
- Incorrect commit timing can cause duplicate processing or message loss.
- `OffsetOutOfRangeException` commonly occurs when retained data has been deleted.
- `auto.offset.reset` determines where new consumers begin reading.
- Monitor Consumer Groups and offset commits continuously.
- Design consumers to tolerate duplicate processing.
- Correct offset management is essential for reliable Kafka applications.