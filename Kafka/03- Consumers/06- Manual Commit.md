# Manual Commit

## Overview

While Auto Commit offers simplicity, many production systems require greater control over when offsets are committed. In such applications, committing an offset before business processing completes could result in data loss.

Kafka solves this problem with **Manual Commit**.

With Manual Commit, the application explicitly decides **when** offsets should be committed. Typically, offsets are committed **only after the application has successfully processed the records**.

Manual Commit provides:

- Better reliability
- Greater control
- Safer recovery
- Stronger delivery guarantees

It is the preferred approach for most production Kafka applications.

---

# What is Manual Commit?

Manual Commit means the application explicitly commits offsets instead of relying on Kafka's background commit mechanism.

Instead of:

```text
Poll

↓

Process

↓

Kafka Commits Automatically
```

The application performs:

```text
Poll

↓

Process

↓

Commit Offset

↓

Next Poll
```

The application controls exactly when the offset is saved.

---

# Why Manual Commit?

Consider an Order Processing Service.

Workflow:

```text
Poll Order

↓

Update Database

↓

Reserve Inventory

↓

Send Email

↓

Commit Offset
```

The offset is committed **only after every business operation succeeds**.

---

# Manual Commit Workflow

```text
Consumer

↓

Poll Records

↓

Deserialize

↓

Business Processing

↓

Successful?

↓

Yes

↓

Commit Offset

↓

Poll Again
```

If processing fails:

```text
No Commit
```

Kafka delivers the message again after recovery.

---

# Disabling Auto Commit

Before using Manual Commit:

```properties
enable.auto.commit=false
```

Kafka stops committing offsets automatically.

The application becomes responsible for committing offsets.

---

# Commit Workflow

```text
Poll

↓

Receive Records

↓

Process Records

↓

Commit Offset

↓

Store Offset

↓

Continue
```

This gives the application complete control.

---

# Why Commit After Processing?

Correct order:

```text
Poll

↓

Process

↓

Commit
```

Incorrect order:

```text
Poll

↓

Commit

↓

Process

↓

Crash
```

If a crash occurs:

```text
Offset Saved

↓

Processing Failed
```

The message is permanently skipped.

---

# Crash Recovery

Suppose:

```text
Offset 150

↓

Process Record

↓

Crash

↓

No Commit
```

After restart:

```text
Resume

↓

Offset 150
```

The message is processed again.

No data is lost.

---

# Processing Success

Suppose processing succeeds.

```text
Poll

↓

Process

↓

Database Updated

↓

Commit Offset
```

Restart:

```text
Resume

↓

Offset 151
```

The consumer continues from the next record.

---

# Processing Failure

Suppose:

```text
Poll

↓

Database Failure
```

Application:

```text
No Commit
```

Restart:

```text
Read Same Message Again
```

The application gets another opportunity to process it.

---

# Manual Commit Architecture

```text
Kafka Topic

↓

Poll Records

↓

Business Logic

↓

Commit Offset

↓

__consumer_offsets
```

Unlike Auto Commit, offsets are stored only when the application explicitly commits them.

---

# Commit Strategies

Kafka supports several manual commit approaches.

```text
commitSync()

or

commitAsync()
```

Each has different characteristics.

---

# Synchronous Commit

The consumer waits until Kafka confirms the commit.

```text
Commit

↓

Broker

↓

ACK

↓

Continue
```

Advantages:

- Reliable
- Easy to understand
- Immediate confirmation

Disadvantages:

- Slightly higher latency
- Blocks the consumer thread

---

# Asynchronous Commit

The consumer sends the commit request and continues immediately.

```text
Commit

↓

Continue Processing

↓

Broker
```

Advantages:

- Higher throughput
- Lower latency

Disadvantages:

- Commit failures require callback handling

---

# Synchronous vs Asynchronous

| commitSync() | commitAsync() |
|--------------|---------------|
| Blocking | Non-blocking |
| Higher latency | Lower latency |
| Simpler recovery | Callback-based recovery |
| Reliable confirmation | Better throughput |

Many production applications combine both approaches.

---

# Batch Processing

Suppose the consumer reads:

```text
Offset 100

↓

101

↓

102

↓

103
```

Application:

```text
Process All Records

↓

Commit Offset 103
```

One commit covers the entire batch.

---

# Commit Frequency

Too frequent:

```text
Every Record

↓

Commit
```

Problems:

- More network requests
- Lower throughput

Too infrequent:

```text
1000 Records

↓

One Commit
```

Problems:

- More duplicate processing after crashes

Choose a balance based on workload.

---

# Manual Commit During Rebalancing

Suppose:

```text
Consumer A

↓

Partition 0
```

Before partitions move:

```text
Commit Offset

↓

Rebalance
```

The new consumer resumes from the latest committed offset.

---

# Manual Commit and Duplicates

Suppose:

```text
Process Record

↓

Crash

↓

No Commit
```

Restart:

```text
Read Record Again
```

Duplicate processing is possible.

Applications should therefore implement **idempotent processing**.

---

# Manual Commit and At-Least-Once Delivery

Manual Commit naturally supports:

```text
Process

↓

Commit
```

If failure occurs before the commit:

```text
Message

↓

Delivered Again
```

This is known as:

```text
At-Least-Once Delivery
```

It is the most common delivery guarantee in Kafka applications.

---

# Performance Considerations

Manual Commit introduces slightly more complexity.

Benefits:

- Better reliability
- Safer recovery
- Controlled commits

Costs:

- Additional application logic
- Slightly more development effort

The reliability benefits usually outweigh the added complexity.

---

# Real-World Example

Payment Service

```text
Poll Payment Event

↓

Update Account Balance

↓

Store Transaction

↓

Generate Receipt

↓

Commit Offset
```

If any step fails:

```text
No Commit

↓

Retry Later
```

No payment event is lost.

---

# Advantages

- Complete control over offset commits.
- Better fault tolerance.
- Prevents premature commits.
- Supports reliable recovery.
- Ideal for critical business applications.
- Works well with transactional workflows.

---

# Limitations

- More application code.
- Incorrect commit logic may cause duplicates.
- Requires understanding of delivery semantics.
- Commit frequency must be carefully tuned.

---

# Suitable Use Cases

Manual Commit is recommended for:

- Banking systems
- Payment services
- Order processing
- Inventory management
- Healthcare applications
- Financial systems
- Event-driven microservices

These applications require reliable processing.

---

# Best Practices

- Disable Auto Commit in production.
- Commit offsets only after successful processing.
- Prefer batch commits over committing every record.
- Handle commit failures appropriately.
- Keep business operations idempotent.
- Monitor commit latency and consumer lag.
- Use synchronous commits when reliability is more important than throughput.

---

# Common Mistakes

- Forgetting to disable Auto Commit.
- Committing offsets before business processing finishes.
- Committing after every record unnecessarily.
- Ignoring commit failures.
- Assuming Manual Commit eliminates duplicate processing.
- Writing non-idempotent business logic.

---

# Summary

Manual Commit gives Kafka consumers full control over when offsets are committed. Unlike Auto Commit, offsets are saved only after successful application processing, significantly reducing the risk of message loss. Although Manual Commit requires additional application logic, it provides stronger delivery guarantees, safer recovery, and is the preferred approach for production systems handling business-critical data.

---

# Key Takeaways

- Manual Commit requires `enable.auto.commit=false`.
- The application explicitly controls when offsets are committed.
- Offsets should be committed only after successful processing.
- `commitSync()` provides reliable blocking commits.
- `commitAsync()` offers better throughput through non-blocking commits.
- Manual Commit supports reliable recovery after failures.
- Duplicate processing is still possible, so business logic should be idempotent.
- Manual Commit is the recommended approach for production Kafka applications handling critical business workflows.