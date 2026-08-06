# Compacted Topics

## Overview

By default, Kafka removes old messages based on **Retention Policies** such as time or storage size. While this works well for event streams, some applications require Kafka to retain the **latest value for every key indefinitely**.

Kafka solves this problem using **Log Compaction**.

Unlike regular retention, Log Compaction preserves the **most recent record for each unique key**, allowing applications to reconstruct the latest state of an entity at any time.

Compacted topics are widely used for:

- User Profiles
- Product Catalogs
- Configuration Data
- Inventory State
- Account Balances
- Kafka Streams State Stores

Understanding Log Compaction is essential when designing stateful event-driven applications.

---

# What is Log Compaction?

Log Compaction is a cleanup strategy where Kafka retains only the latest record for each message key.

Instead of deleting messages based solely on age, Kafka removes older versions of the same key.

Example:

```text
Customer ID = 101

↓

Version 1

↓

Version 2

↓

Version 3
```

After compaction:

```text
Customer ID = 101

↓

Version 3
```

Only the newest record remains.

---

# Why Log Compaction Exists

Consider a customer profile.

Updates occur over time.

```text
Customer

↓

Name Updated

↓

Address Updated

↓

Phone Updated

↓

Email Updated
```

A new application joining later only needs the **latest customer information**, not every historical change.

Compaction provides exactly that.

---

# Regular Retention vs Log Compaction

### Regular Retention

```text
Message

↓

Store

↓

Retention Time Expires

↓

Delete
```

---

### Log Compaction

```text
Message

↓

Store

↓

New Record Same Key

↓

Old Record Removed
```

The latest value always survives.

---

# Compaction Workflow

```text
Producer

↓

Topic

↓

Multiple Updates

↓

Log Cleaner

↓

Latest Record Per Key
```

Kafka performs compaction in the background.

---

# Example Without Compaction

```text
Offset

0

Customer A

Version 1

----------------

Offset

1

Customer A

Version 2

----------------

Offset

2

Customer A

Version 3
```

All versions remain until retention removes them.

---

# Example With Compaction

After compaction:

```text
Customer A

↓

Version 3
```

Versions 1 and 2 are eventually removed.

---

# Why Message Keys Matter

Compaction works **only** on keyed messages.

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
NULL Key
```

Kafka cannot determine which records belong together.

---

# How Kafka Identifies Duplicate Keys

Suppose:

```text
Key = 101

Value = Alice

----------------

Key = 101

Value = Alice Smith

----------------

Key = 101

Value = Alice Johnson
```

Kafka eventually retains:

```text
Key = 101

Value = Alice Johnson
```

---

# Log Cleaner

Kafka uses a background process called the **Log Cleaner**.

Workflow:

```text
Kafka Log

↓

Log Cleaner

↓

Remove Old Versions

↓

Compact Log
```

Applications do not perform compaction manually.

---

# Message Ordering

Compaction does **not** change ordering.

Before:

```text
Offset

10

↓

11

↓

12
```

After compaction:

Remaining messages preserve their original offsets.

Offsets are never renumbered.

---

# Tombstone Records

Kafka supports record deletion using **Tombstone Messages**.

Example:

```text
Key = Customer101

Value = NULL
```

This tells Kafka:

```text
Delete

Customer101
```

During compaction:

```text
Latest Record

↓

NULL

↓

Remove Key
```

---

# Tombstone Workflow

```text
Customer Exists

↓

Tombstone Record

↓

Log Cleaner

↓

Customer Removed
```

This is how deletions are represented in compacted topics.

---

# Cleanup Policy

Compaction is enabled using:

```properties
cleanup.policy=compact
```

Kafka now performs log compaction.

---

# Mixed Cleanup Policy

Kafka also supports:

```properties
cleanup.policy=compact,delete
```

Meaning:

```text
Keep Latest Record

+

Apply Retention Rules
```

Useful when applications need both replay capability and bounded storage.

---

# Common Use Cases

Compacted topics are ideal for:

- Customer Profiles
- Product Catalogs
- Configuration Data
- Inventory Quantities
- Feature Flags
- User Preferences
- Device Status
- Account Information

These datasets represent the **latest state** rather than an immutable event history.

---

# When Not to Use Compaction

Avoid compaction for immutable business events.

Examples:

```text
Orders

Payments

Invoices

Audit Logs
```

Historical records should never disappear.

Regular retention is more appropriate.

---

# Event Sourcing vs State Storage

### Event Stream

```text
Order Created

↓

Payment Received

↓

Order Shipped
```

Every event is important.

---

### State Store

```text
Customer

↓

Version 1

↓

Version 2

↓

Version 3
```

Only the latest state matters.

Compacted topics are designed for the second scenario.

---

# Compaction Architecture

```text
               Producer
                    │
                    ▼
            Compacted Topic
                    │
                    ▼
            Multiple Updates
                    │
                    ▼
             Log Cleaner
                    │
                    ▼
      Latest Record Per Key
```

---

# Real-World Example

Inventory Service:

```text
Product A

↓

Quantity = 100

↓

Quantity = 95

↓

Quantity = 90

↓

Quantity = 75
```

After compaction:

```text
Product A

↓

Quantity = 75
```

Applications rebuilding inventory state only need the latest quantity.

---

# Retention vs Compaction

| Feature | Retention | Compaction |
|----------|-----------|------------|
| Deletes by Time | ✅ | ❌ |
| Deletes by Size | ✅ | ❌ |
| Keeps Latest Value | ❌ | ✅ |
| Requires Message Keys | ❌ | ✅ |
| Preserves Event History | ✅ | ❌ |
| Ideal for State Data | ❌ | ✅ |

---

# Advantages

- Keeps the latest state for every key.
- Supports application recovery.
- Reduces storage usage.
- Enables fast state reconstruction.
- Works well with Kafka Streams.
- Removes obsolete records automatically.

---

# Limitations

- Requires message keys.
- Older versions are eventually removed.
- Not suitable for immutable event histories.
- Compaction occurs asynchronously, not immediately.

---

# Best Practices

- Always use meaningful message keys.
- Use compaction only for state-based data.
- Combine `compact,delete` when both state and retention are required.
- Understand that compaction is asynchronous.
- Use tombstone records for deletions.
- Document which topics use compaction.
- Monitor Log Cleaner performance.

---

# Common Mistakes

- Expecting compaction to happen immediately.
- Using compacted topics for audit logs.
- Producing records without keys.
- Assuming offsets change after compaction.
- Confusing retention with compaction.
- Forgetting that tombstones are required for deletions.

---

# Summary

Log Compaction is Kafka's mechanism for retaining the latest record for each message key while removing obsolete versions. Unlike traditional retention, which deletes data based on time or size, compaction preserves the current state of entities, making it ideal for configuration data, inventory, user profiles, and stateful stream processing. By combining keyed messages, tombstone records, and Kafka's background Log Cleaner, compacted topics provide an efficient way to maintain continuously evolving datasets while minimizing storage usage.

---

# Key Takeaways

- Log Compaction retains the latest record for each message key.
- Compaction requires every record to have a key.
- Kafka performs compaction asynchronously using the Log Cleaner.
- Tombstone records (`value = null`) represent deletions.
- Compacted topics are ideal for state-based data rather than immutable event streams.
- Regular retention and log compaction serve different purposes.
- Offsets remain unchanged after compaction.
- Log Compaction is widely used for configuration management, state stores, and Kafka Streams applications.