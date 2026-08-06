# Log Segments

## Overview

Apache Kafka stores every partition as an **append-only log**. However, Kafka does not store the entire partition in a single massive file. Instead, it divides each partition into multiple smaller files called **Log Segments**.

Log Segments make Kafka highly efficient by enabling:

- Fast writes
- Efficient disk management
- Easy message retention
- Log compaction
- Quick recovery after failures

Without log segments, Kafka would eventually create enormous log files that would be difficult to manage and maintain.

---

# What is a Log Segment?

A log segment is a physical file on disk that stores a portion of a partition's messages.

Instead of:

```text
Partition 0

One Huge File

──────────────────────────
Offset 0
Offset 1
Offset 2
...
Offset 1,000,000
──────────────────────────
```

Kafka stores:

```text
Partition 0

Segment 1

Offset 0
Offset 1
...
Offset 999

----------------------

Segment 2

Offset 1000
Offset 1001
...
Offset 1999

----------------------

Segment 3

Offset 2000
Offset 2001
...
Offset 2999
```

Each segment stores a continuous range of offsets.

---

# Why Does Kafka Use Log Segments?

Imagine a partition storing 500 GB of data.

Without segments:

```text
Partition

↓

500 GB File
```

Problems:

- Difficult to delete old data
- Slow recovery
- Large file management
- Poor operating system performance

Instead, Kafka divides the partition into manageable pieces.

```text
Partition

↓

Segment A

Segment B

Segment C

Segment D
```

This makes storage much more efficient.

---

# Partition and Log Segments

Every partition consists of multiple log segments.

```text
Orders Topic

Partition 0

│

├── Segment 1

├── Segment 2

├── Segment 3

└── Active Segment
```

Only one segment is active for writes.

Older segments become read-only.

---

# Active Segment

Kafka always writes new messages to the **active segment**.

Example:

```text
Partition 0

Segment 1

(Read Only)

-------------------

Segment 2

(Read Only)

-------------------

Segment 3

Active

↓

New Messages
```

When the active segment reaches a configured limit, Kafka creates a new active segment.

---

# Segment Rolling

Kafka periodically creates new segments.

This process is called **Segment Rolling**.

Example:

```text
Current Active Segment

↓

Size Reaches Limit

↓

Close Segment

↓

Create New Active Segment
```

The previous segment becomes read-only.

The new segment receives future messages.

---

# When Does Kafka Create a New Segment?

Kafka rolls a segment when:

- Segment reaches the configured size.
- Segment reaches the configured age.
- Broker restarts.
- Log rolling is triggered manually.

---

# Segment Files

Each log segment consists of multiple files.

Example:

```text
00000000000000000000.log

00000000000000000000.index

00000000000000000000.timeindex
```

These files work together to provide fast reads and efficient storage.

---

# Log File

The `.log` file stores the actual messages.

Example:

```text
Offset 0

Order Created

----------------

Offset 1

Payment Completed

----------------

Offset 2

Order Shipped
```

This is where Kafka persists event data.

---

# Index File

Kafka does not scan the log file sequentially every time.

Instead, it maintains an index.

```text
Offset

↓

Physical Location

↓

Read Message
```

The index allows Kafka to quickly locate messages.

---

# Time Index

Kafka also maintains a timestamp index.

Example:

```text
Timestamp

↓

Segment Location
```

This enables efficient time-based lookups.

For example:

> Read messages after 10:30 AM.

Kafka can quickly locate the correct segment.

---

# Segment Lifecycle

A log segment typically follows this lifecycle.

```text
Created

↓

Active

↓

Read Only

↓

Retention Check

↓

Deleted or Compacted
```

Older segments remain available until Kafka's cleanup policy removes them.

---

# Log Segments and Retention

Suppose retention is set to:

```text
7 Days
```

Kafka evaluates segments individually.

Example:

```text
Segment 1

10 Days Old

↓

Delete

------------------

Segment 2

5 Days Old

↓

Keep

------------------

Segment 3

1 Day Old

↓

Keep
```

Kafka deletes the entire segment rather than individual messages.

This makes retention extremely efficient.

---

# Log Segments and Log Compaction

When log compaction is enabled:

```text
Segment

↓

Duplicate Keys

↓

Keep Latest Version

↓

Compact Segment
```

Instead of deleting the entire segment, Kafka removes obsolete records while preserving the latest value for each key.

---

# Segment Size

Kafka controls segment size using configuration.

Example:

```properties
log.segment.bytes=1073741824
```

This creates segments of approximately:

```text
1 GB
```

Larger segments:

- Fewer files
- Less metadata
- Slower retention cleanup

Smaller segments:

- More files
- Faster cleanup
- Slightly more overhead

Choosing the right size depends on workload.

---

# Log Segments and Recovery

Suppose the broker crashes.

```text
Broker

↓

Restart
```

Kafka only needs to recover the active segment.

Older read-only segments are already complete.

This significantly reduces recovery time.

---

# Advantages of Log Segments

- Efficient disk usage
- Fast sequential writes
- Efficient retention cleanup
- Faster broker recovery
- Simplified log compaction
- Better operating system performance

---

# Common Misconceptions

### "A partition is a single file."

Incorrect.

A partition consists of multiple log segments.

---

### "Kafka deletes individual messages."

Incorrect.

Kafka usually deletes entire log segments.

---

### "Kafka constantly rewrites log files."

Incorrect.

Kafka appends new messages to the active segment.

Older segments remain immutable until cleanup.

---

# Best Practices

- Use Kafka's default segment settings unless workload analysis suggests otherwise.
- Monitor disk utilization regularly.
- Configure retention policies based on business requirements.
- Understand how segment size affects cleanup performance.
- Avoid unnecessarily small segment sizes in production.

---

# Common Mistakes

- Confusing partitions with log segments.
- Assuming every message is stored in a separate file.
- Ignoring the impact of segment size on retention.
- Assuming Kafka deletes messages one by one.
- Misunderstanding the relationship between segments and log compaction.

---

# Summary

Kafka stores each partition as a collection of log segments rather than one large file. New messages are appended to the active segment, while older segments become read-only. Segment rolling, retention, and compaction allow Kafka to efficiently manage storage, perform fast sequential writes, recover quickly from failures, and delete old data with minimal overhead. Log segments are a key reason why Kafka can scale to handle massive volumes of data efficiently.

---

# Key Takeaways

- A partition is made up of multiple log segments.
- Kafka writes only to the active segment.
- Older segments become read-only.
- Segment rolling creates new active segments when size or time limits are reached.
- Kafka stores data in `.log`, `.index`, and `.timeindex` files.
- Retention usually deletes entire log segments rather than individual messages.
- Log compaction operates on log segments to retain the latest value for each key.
- Log segments enable Kafka's high write throughput, efficient storage management, and fast recovery.