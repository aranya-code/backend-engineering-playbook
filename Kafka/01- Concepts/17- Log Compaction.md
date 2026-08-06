# Log Compaction

## Overview

While retention policies remove old data based on **time** or **storage size**, some applications require Kafka to always retain the **latest state** of every record.

For example:

- User profiles
- Product catalog
- Account balances
- Configuration data
- Device status

In these scenarios, deleting data purely based on time may not be desirable.

Apache Kafka solves this using **Log Compaction**, a cleanup mechanism that retains **only the latest record for each unique message key** while removing older versions.

Log compaction allows Kafka to behave like a continuously updated database while still maintaining its append-only log architecture.

---

# What is Log Compaction?

Log Compaction is a cleanup policy that removes older records having the same message key.

Consider the following messages.

```text
Key: User 101

Version 1

--------------------

Key: User 101

Version 2

--------------------

Key: User 101

Version 3
```

After compaction:

```text
Key: User 101

Version 3
```

Only the latest version remains.

---

# Why Do We Need Log Compaction?

Suppose an application stores user profiles.

Updates occur throughout the day.

```text
User 101

↓

Name Updated

↓

Address Updated

↓

Phone Updated

↓

Email Updated
```

Without compaction:

```text
Version 1

Version 2

Version 3

Version 4
```

The log continues growing indefinitely.

With compaction:

```text
User 101

↓

Latest Version Only
```

Kafka keeps the most recent state.

---

# How Log Compaction Works

Kafka continuously appends new messages.

```text
Offset 0

User 101 → Version 1

-------------------

Offset 1

User 102 → Version 1

-------------------

Offset 2

User 101 → Version 2

-------------------

Offset 3

User 103 → Version 1

-------------------

Offset 4

User 101 → Version 3
```

After compaction:

```text
User 101 → Version 3

User 102 → Version 1

User 103 → Version 1
```

Older versions of User 101 are removed.

---

# Append-Only Log

Even with log compaction enabled, Kafka never overwrites existing records.

Instead:

```text
Producer

↓

Append New Record

↓

Later

↓

Background Compaction
```

Messages are always appended first.

Compaction occurs asynchronously.

---

# Message Keys are Mandatory

Log compaction works only when messages have keys.

Example:

```text
Key

Customer ID

↓

Value

Customer Details
```

Without a key:

```text
Key = null
```

Kafka cannot determine which records belong together.

Therefore, null-key messages are not compacted.

---

# Real-World Example

Consider a product catalog.

```text
Product 501

Price = ₹100

--------------------

Product 501

Price = ₹120

--------------------

Product 501

Price = ₹140
```

After compaction:

```text
Product 501

Price = ₹140
```

Applications rebuilding the catalog only need the latest value.

---

# Tombstone Records

Sometimes data needs to be deleted completely.

Kafka uses a special record called a **Tombstone Record**.

Example:

```text
Key

User 101

Value

null
```

The null value tells Kafka:

```text
Delete This Key
```

After compaction, both the previous records and the tombstone are eventually removed.

---

# Compaction Workflow

```text
Producer

↓

Append Message

↓

Append Updated Message

↓

Append Updated Message

↓

Background Compaction

↓

Keep Latest Version
```

Compaction runs periodically.

It is not performed immediately after every write.

---

# Log Compaction vs Retention

These two concepts solve different problems.

| Log Retention | Log Compaction |
|---------------|----------------|
| Deletes old data based on time or size | Removes older records with the same key |
| Entire log segments are deleted | Individual records are removed during compaction |
| Suitable for event history | Suitable for maintaining latest state |
| Message history eventually disappears | Latest version of every key is preserved |

---

# Example Comparison

### Retention

```text
Day 1

User Updated

-------------------

Day 8

Retention Expired

↓

Delete Entire Segment
```

---

### Log Compaction

```text
User Updated

↓

User Updated Again

↓

User Updated Again

↓

Keep Latest Version
```

History is reduced, but the latest state remains.

---

# Common Use Cases

Log compaction is commonly used for:

- User profiles
- Product catalogs
- Customer information
- Device configurations
- Application settings
- Shopping cart state
- Inventory status
- Account balances

These systems care about the current state rather than the complete history.

---

# Event Sourcing Example

Suppose a customer's address changes several times.

```text
Address A

↓

Address B

↓

Address C

↓

Address D
```

After compaction:

```text
Address D
```

Any new consumer rebuilding state immediately receives the latest address.

---

# Topic Configuration

Log compaction is enabled using the cleanup policy.

Example:

```properties
cleanup.policy=compact
```

Kafka also supports combining retention and compaction.

Example:

```properties
cleanup.policy=compact,delete
```

This allows Kafka to:

- Compact duplicate records.
- Remove very old data based on retention settings.

---

# Advantages

- Maintains the latest state for every key.
- Reduces storage usage.
- Enables fast state reconstruction.
- Supports event sourcing patterns.
- Ideal for configuration and reference data.
- Improves storage efficiency.

---

# Limitations

- Requires message keys.
- Does not preserve complete history.
- Runs asynchronously.
- More CPU intensive than simple retention.
- Not suitable for applications requiring every historical event.

---

# Best Practices

- Always use meaningful message keys.
- Use log compaction only for state-based topics.
- Continue using standard retention for event history topics.
- Monitor compaction performance.
- Use tombstone records for deletions.
- Combine compaction and retention when appropriate.

---

# Common Mistakes

- Expecting compaction to happen immediately.
- Using null keys with compacted topics.
- Assuming compaction preserves every event.
- Using compaction for audit logs or financial transaction history.
- Confusing log compaction with retention policies.

---

# Summary

Log compaction is a Kafka cleanup mechanism that preserves only the latest record for each unique message key while removing older versions. Unlike retention policies, which delete data based on time or size, log compaction focuses on maintaining the most recent state of each entity. It is particularly useful for applications such as user profiles, configuration management, product catalogs, and event-sourced systems where the latest state is more valuable than the complete history.

---

# Key Takeaways

- Log compaction retains only the latest record for each message key.
- Messages must have keys for compaction to work.
- Kafka always appends new records before compacting older ones.
- Compaction runs asynchronously in the background.
- Tombstone records are used to delete keys from compacted topics.
- Log compaction and retention solve different problems.
- Compaction is ideal for state-based data such as user profiles and configuration.
- Event history and audit logs typically use retention rather than log compaction.