# Auto Commit

## Overview

One of the most important decisions when building a Kafka consumer is **when offsets should be committed**.

Kafka provides two offset commit strategies:

- Auto Commit
- Manual Commit

With **Auto Commit**, the Kafka consumer periodically commits offsets automatically in the background without explicit application code.

Auto Commit is simple to use and is suitable for applications where occasional duplicate processing or message loss is acceptable. However, it is not recommended for business-critical systems because offset commits are independent of business logic execution.

Understanding how Auto Commit works is essential before learning Manual Commit.

---

# What is Auto Commit?

Auto Commit is a Kafka feature where the consumer periodically commits processed offsets automatically.

Instead of:

```text
Poll

↓

Process

↓

Commit Offset
```

Kafka performs:

```text
Poll

↓

Process

↓

Background Auto Commit
```

The application does not explicitly commit offsets.

---

# Why Auto Commit Exists

Managing offsets manually can be tedious.

Without Auto Commit:

```text
Process Record

↓

Commit Offset

↓

Process Next Record

↓

Commit Offset
```

Kafka simplifies this by periodically committing offsets automatically.

This makes consumer implementation much easier.

---

# Auto Commit Workflow

```text
Consumer

↓

Poll Records

↓

Process Records

↓

Auto Commit Timer

↓

Commit Offsets

↓

Repeat
```

The consumer continues processing while commits happen periodically.

---

# Enabling Auto Commit

Auto Commit is enabled using:

```properties
enable.auto.commit=true
```

This is the default behavior for Kafka consumers.

---

# Auto Commit Interval

Kafka commits offsets at a fixed interval.

Configuration:

```properties
auto.commit.interval.ms=5000
```

Equivalent:

```text
5 Seconds
```

Every five seconds Kafka commits the latest consumed offsets.

---

# Auto Commit Timeline

Suppose the consumer reads:

```text
Offset 100

↓

Offset 101

↓

Offset 102
```

Timeline:

```text
0 Seconds

↓

Read Records

↓

Process Records

↓

5 Seconds

↓

Auto Commit
```

The committed offset advances automatically.

---

# Internal Workflow

The complete workflow:

```text
Poll

↓

Receive Records

↓

Application Processes

↓

Auto Commit Timer

↓

Commit Offset

↓

Continue Polling
```

The application never explicitly calls a commit method.

---

# Auto Commit Example

Suppose:

```text
Current Offset

250
```

After five seconds:

```text
Kafka

↓

Commit Offset

250
```

Next poll continues from:

```text
Offset

251
```

---

# Crash Scenario

Suppose:

```text
Poll

↓

Offset 100

↓

Offset 101

↓

Auto Commit

↓

Crash
```

After restart:

```text
Resume

↓

Offset 102
```

Everything works correctly.

---

# Problem Scenario

Suppose processing is slow.

```text
Poll

↓

Offset 100

↓

Auto Commit

↓

Business Logic Running

↓

Crash
```

Offset 100 has already been committed.

However:

```text
Business Logic

Not Completed
```

After restart:

```text
Resume

↓

Offset 101
```

Offset 100 is skipped.

The message is lost from the application's perspective.

---

# Visual Example

Incorrect sequence:

```text
Poll

↓

Auto Commit

↓

Database Update

↓

Crash
```

Result:

```text
Database

Not Updated

↓

Offset Already Committed
```

Kafka believes processing succeeded.

---

# Correct Sequence (Ideal)

```text
Poll

↓

Process Successfully

↓

Commit Offset
```

This guarantees offsets represent completed work.

Auto Commit cannot always guarantee this ordering.

---

# Auto Commit During Rebalancing

Suppose:

```text
Consumer A

↓

Partition 0
```

A rebalance occurs.

Before partitions move:

```text
Auto Commit

↓

Latest Offset Saved
```

The new consumer resumes from the committed offset.

---

# Auto Commit and Duplicates

Suppose:

```text
Process Record

↓

Crash

↓

No Auto Commit Yet
```

Restart:

```text
Read Same Record Again
```

Duplicate processing occurs.

Applications should therefore be idempotent.

---

# Auto Commit and Message Loss

Suppose:

```text
Auto Commit

↓

Business Logic

↓

Crash
```

Message processing never completed.

Yet Kafka has already committed the offset.

Result:

```text
Message Lost
```

This is the biggest drawback of Auto Commit.

---

# Auto Commit Architecture

```text
               Kafka Topic
                     │
                     ▼
              Consumer Poll
                     │
                     ▼
             Process Records
                     │
                     ▼
          Auto Commit Timer
                     │
                     ▼
        __consumer_offsets
```

The timer operates independently of application logic.

---

# Advantages

- Very simple configuration.
- No commit code required.
- Good for prototypes.
- Lower implementation complexity.
- Suitable for lightweight consumers.

---

# Limitations

- Offsets may be committed before processing finishes.
- Possible message loss.
- Possible duplicate processing.
- Less control over recovery.
- Not ideal for critical business workflows.

---

# Suitable Use Cases

Auto Commit is appropriate for:

- Log processing
- Metrics collection
- Monitoring systems
- Development environments
- Simple analytics

These workloads can tolerate occasional duplicates or missed records.

---

# When Not to Use Auto Commit

Avoid Auto Commit for:

- Banking systems
- Payment processing
- Inventory management
- Financial transactions
- Order processing
- Healthcare systems

These applications require precise control over offset commits.

---

# Auto Commit Configuration

Typical configuration:

```properties
enable.auto.commit=true

auto.commit.interval.ms=5000
```

Kafka automatically commits offsets every five seconds.

---

# Auto Commit vs Manual Commit

| Auto Commit | Manual Commit |
|--------------|---------------|
| Automatic | Application controlled |
| Simple | More complex |
| Less reliable | More reliable |
| Lower control | Complete control |
| Suitable for simple workloads | Suitable for critical systems |

Manual Commit provides stronger delivery guarantees and greater flexibility.

---

# Best Practices

- Use Auto Commit only when occasional duplicates or message loss are acceptable.
- Keep message processing reasonably fast.
- Design processing logic to be idempotent.
- Monitor consumer lag and processing failures.
- Switch to Manual Commit for business-critical applications.
- Understand the impact of the commit interval on recovery.

---

# Common Mistakes

- Assuming Auto Commit commits offsets immediately after processing.
- Using Auto Commit for financial or transactional systems.
- Ignoring the possibility of message loss.
- Believing Auto Commit guarantees exactly-once processing.
- Performing long-running business logic while relying on Auto Commit.

---

# Summary

Auto Commit automatically commits consumer offsets at regular intervals without requiring explicit application code. While this simplifies consumer development, commits occur independently of business logic execution, creating the possibility of duplicate processing or message loss during failures. Auto Commit is well suited for simple, non-critical workloads, whereas applications requiring precise delivery guarantees should use Manual Commit.

---

# Key Takeaways

- Auto Commit automatically commits offsets at regular intervals.
- It is enabled using `enable.auto.commit=true`.
- The commit frequency is controlled by `auto.commit.interval.ms`.
- Offset commits occur independently of application processing.
- Auto Commit simplifies consumer development.
- It may lead to duplicate processing or message loss during failures.
- Auto Commit is suitable for non-critical workloads.
- Business-critical applications should generally prefer Manual Commit.