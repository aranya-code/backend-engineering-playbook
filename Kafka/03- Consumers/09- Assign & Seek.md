# Assign & Seek

## Overview

By default, Kafka consumers participate in a **Consumer Group**, where Kafka automatically assigns partitions and manages offsets.

However, there are situations where applications need complete control over:

- Which partitions to read
- Where to start reading
- Replaying historical data
- Skipping messages
- Reading specific offsets

Kafka provides two powerful APIs for these use cases:

- **Assign**
- **Seek**

Unlike Consumer Groups, these APIs allow applications to manually control partition assignment and reading positions.

They are commonly used in:

- Data replay
- Recovery tools
- Debugging
- Batch processing
- Data migration
- Audit applications

---

# Automatic vs Manual Assignment

By default:

```text
Consumer

↓

Join Consumer Group

↓

Kafka Assigns Partitions
```

Using Assign:

```text
Consumer

↓

Application Assigns Partitions
```

The application becomes responsible for partition selection.

---

# What is Assign?

The **Assign API** allows a consumer to manually subscribe to specific partitions.

Instead of:

```text
Orders Topic

↓

All Partitions
```

You can explicitly choose:

```text
Orders Topic

↓

Partition 2
```

Kafka does not perform automatic assignment.

---

# Why Use Assign?

Some applications require deterministic partition access.

Examples:

- Replay Partition 5
- Recover failed records
- Audit historical events
- Read a single partition
- Batch processing

Consumer Groups are unnecessary for these workloads.

---

# Assign Workflow

```text
Application

↓

Assign Partition

↓

Poll Records

↓

Process Records
```

No Group Coordinator is involved.

---

# Assign Example

Suppose a topic contains:

```text
Orders Topic

Partition 0

Partition 1

Partition 2

Partition 3
```

Application:

```text
Assign

↓

Partition 2
```

The consumer only reads:

```text
Partition 2
```

---

# Multiple Partition Assignment

Applications may assign multiple partitions.

Example:

```text
Assign

↓

Partition 0

Partition 3
```

The consumer reads only those partitions.

---

# Assign Architecture

```text
Application

↓

Assign()

↓

Partition

↓

Poll()

↓

Records
```

Kafka skips consumer group management completely.

---

# Assign vs Subscribe

Kafka provides two ways to receive partitions.

| Subscribe | Assign |
|------------|---------|
| Uses Consumer Groups | No Consumer Groups |
| Automatic Assignment | Manual Assignment |
| Supports Rebalancing | No Rebalancing |
| Dynamic | Static |
| Production Streaming | Replay & Utilities |

---

# Limitations of Assign

Because there is no Consumer Group:

- No automatic scaling
- No rebalancing
- No fault tolerance
- No automatic partition distribution

Applications manage everything manually.

---

# What is Seek?

While Assign chooses **which partition** to read,

**Seek** chooses **where to start reading**.

Example:

```text
Partition

↓

Offset 250
```

Consumer:

```text
Seek

↓

Offset 150
```

Reading resumes from Offset 150.

---

# Why Seek?

Seek allows consumers to:

- Replay messages
- Skip messages
- Recover failures
- Read historical events
- Restart processing

This is extremely useful in production support.

---

# Seek Workflow

```text
Assign Partition

↓

Seek Offset

↓

Poll Records
```

The consumer starts from the requested offset.

---

# Seek Example

Partition:

```text
Offset

100

101

102

103

104
```

Application:

```text
Seek

↓

102
```

Consumer reads:

```text
102

103

104
```

---

# Seek to Beginning

Applications may restart from the first available record.

```text
Seek

↓

Beginning
```

Result:

```text
Offset 0
```

Useful for:

- Full replay
- Data migration
- Testing

---

# Seek to End

Applications may skip historical records.

```text
Seek

↓

End
```

Consumer reads only future messages.

---

# Seek to Specific Offset

Example:

```text
Seek

↓

Offset 500
```

Processing resumes exactly at Offset 500.

---

# Replay Messages

Suppose:

```text
Offset

100

↓

200
```

Application:

```text
Seek

↓

100
```

Kafka replays all messages.

This is commonly used for debugging.

---

# Skip Corrupted Records

Suppose:

```text
Offset 250

↓

Corrupted
```

Application:

```text
Seek

↓

251
```

Processing continues from the next record.

---

# Assign and Seek Together

Most applications combine both APIs.

```text
Assign Partition

↓

Seek Offset

↓

Poll

↓

Process
```

Assign determines **where** to read.

Seek determines **from where** to read.

---

# Recovery Example

Suppose processing failed.

```text
Offset

520
```

Application:

```text
Assign

↓

Partition 3

↓

Seek

↓

520

↓

Retry Processing
```

No other records are affected.

---

# Historical Data Processing

Suppose analytics requires last week's data.

```text
Assign

↓

Partition

↓

Seek

↓

Old Offset

↓

Replay
```

The consumer processes historical events again.

---

# Consumer Group vs Assign

Consumer Group:

```text
Kafka

↓

Partition Assignment

↓

Consumer
```

Assign:

```text
Application

↓

Partition Assignment

↓

Consumer
```

Responsibility shifts from Kafka to the application.

---

# Offset Management

Assign does not disable offset commits.

Applications may still:

```text
Poll

↓

Process

↓

Commit Offset
```

Or choose not to commit at all.

---

# Performance Considerations

Assign avoids:

- Group Coordinator
- Rebalancing
- Heartbeats

Benefits:

- Lower overhead
- Predictable partition ownership

Trade-off:

- Manual management

---

# Real-World Use Cases

Assign and Seek are commonly used for:

- Log replay
- Data migration
- Disaster recovery
- Audit systems
- Historical analytics
- Debugging
- ETL pipelines
- Administrative tools

---

# Advantages

- Complete partition control.
- Read any offset.
- Replay historical events.
- Skip problematic records.
- No consumer group dependency.
- Ideal for maintenance and utility applications.

---

# Limitations

- No automatic partition assignment.
- No load balancing.
- No rebalancing.
- No automatic failover.
- More application logic.

---

# Best Practices

- Use Subscribe for normal streaming applications.
- Use Assign for replay and administrative tools.
- Use Seek for controlled reprocessing.
- Validate offsets before seeking.
- Document replay procedures.
- Monitor processing progress during replays.

---

# Common Mistakes

- Using Assign in scalable consumer applications.
- Expecting rebalancing when using Assign.
- Seeking beyond the available offset range.
- Forgetting that Assign bypasses Consumer Groups.
- Replaying production data without understanding business impact.

---

# Summary

Assign and Seek provide low-level control over Kafka consumer behavior. The Assign API allows applications to manually select the partitions they want to consume, bypassing Consumer Groups and automatic partition assignment. The Seek API allows consumers to reposition their reading location to any valid offset, making it possible to replay historical events, skip problematic records, or recover from failures. Together, these APIs are invaluable for operational tooling, debugging, data migration, and recovery workflows where precise control over message consumption is required.

---

# Key Takeaways

- Assign manually selects which partitions a consumer reads.
- Seek manually selects where reading begins within a partition.
- Assign bypasses Consumer Groups and rebalancing.
- Seek supports replay, recovery, and historical data processing.
- Assign and Seek are commonly used together.
- Consumer Groups remain the preferred choice for scalable streaming applications.
- Assign is ideal for administrative and utility applications.
- Seek enables precise offset control for debugging and data recovery.