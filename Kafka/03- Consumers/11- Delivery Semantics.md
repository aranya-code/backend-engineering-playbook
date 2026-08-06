# Delivery Semantics

## Overview

One of the most important questions in any messaging system is:

> **What happens if a failure occurs while processing a message?**

Imagine a payment processing system.

A consumer receives a payment event, updates the database, and then crashes before committing its offset.

Should Kafka deliver the message again?

Should it skip the message?

Should it guarantee the message is processed exactly once?

These guarantees are known as **Delivery Semantics**.

Kafka supports three delivery guarantees:

- At Most Once
- At Least Once
- Exactly Once

Each provides different trade-offs between reliability, performance, and complexity.

Understanding these semantics is essential for designing reliable event-driven systems.

---

# What are Delivery Semantics?

Delivery Semantics describe **how many times a consumer may process a message** under normal operation and during failures.

Possible outcomes:

```text
Never

↓

Once

↓

Multiple Times
```

Kafka provides mechanisms to control these behaviors.

---

# Why Delivery Semantics Matter

Consider an online payment.

```text
Payment Received

↓

Update Balance

↓

Commit Offset
```

If the application crashes during processing:

- Was the payment processed?
- Should Kafka resend it?
- Will it be duplicated?

The chosen delivery guarantee determines the answer.

---

# Three Delivery Guarantees

Kafka supports three delivery models.

```text
At Most Once

↓

At Least Once

↓

Exactly Once
```

Each offers different reliability characteristics.

---

# At Most Once Delivery

Definition:

```text
Message

↓

Delivered

↓

Never Delivered Again
```

A message may be lost, but it is never processed twice.

---

# Workflow

```text
Poll

↓

Commit Offset

↓

Process Message
```

Notice that the offset is committed **before** processing.

---

# Failure Example

```text
Poll

↓

Commit Offset

↓

Crash
```

After restart:

```text
Next Offset
```

The original message is skipped.

Result:

```text
Message Lost
```

---

# Characteristics

Advantages:

- Fastest processing
- No duplicate processing
- Simple implementation

Disadvantages:

- Possible message loss

---

# Suitable Use Cases

- Monitoring
- Metrics collection
- Temporary analytics
- Log aggregation

Occasional message loss is acceptable.

---

# At Least Once Delivery

Definition:

```text
Every Message

↓

Processed

At Least Once
```

No message is lost.

However, duplicates are possible.

---

# Workflow

```text
Poll

↓

Process Message

↓

Commit Offset
```

The offset is committed only after successful processing.

---

# Failure Example

```text
Poll

↓

Process

↓

Crash

↓

No Commit
```

Restart:

```text
Read Same Message Again
```

Result:

```text
Duplicate Processing
```

No data is lost.

---

# Characteristics

Advantages:

- No message loss
- High reliability
- Most commonly used

Disadvantages:

- Duplicate processing possible

Applications should therefore be idempotent.

---

# Suitable Use Cases

- Order Processing
- Inventory Systems
- Payment Processing
- Banking
- Microservices

This is the default choice for most production Kafka consumers.

---

# Exactly Once Delivery

Definition:

```text
One Message

↓

Processed Exactly Once
```

No duplicates.

No message loss.

---

# Workflow

```text
Producer Transaction

↓

Kafka

↓

Consumer

↓

Transactional Processing

↓

Commit
```

Exactly Once requires cooperation between:

- Producer
- Broker
- Consumer

---

# Exactly Once Requirements

Kafka combines several technologies.

```text
Idempotent Producer

+

Transactions

+

Offset Management

=

Exactly Once
```

All three are required.

---

# Exactly Once Example

Suppose:

```text
Process Payment

↓

Update Database

↓

Commit Transaction

↓

Commit Offset
```

If failure occurs:

```text
Rollback

↓

Retry
```

Kafka guarantees consistent results.

---

# Delivery Semantics Comparison

| Feature | At Most Once | At Least Once | Exactly Once |
|----------|--------------|---------------|--------------|
| Message Loss | Possible | No | No |
| Duplicate Processing | No | Possible | No |
| Reliability | Low | High | Highest |
| Complexity | Low | Medium | High |
| Performance | Highest | High | Lower |
| Production Usage | Limited | Very Common | Specialized |

---

# Offset Commit Timing

Delivery guarantees depend largely on **when offsets are committed**.

### At Most Once

```text
Commit

↓

Process
```

Possible message loss.

---

### At Least Once

```text
Process

↓

Commit
```

Possible duplicates.

---

### Exactly Once

```text
Process

↓

Transaction

↓

Commit Offset

↓

Commit Transaction
```

No duplicates.

No loss.

---

# Delivery Timeline

### At Most Once

```text
Poll

↓

Commit

↓

Process
```

---

### At Least Once

```text
Poll

↓

Process

↓

Commit
```

---

### Exactly Once

```text
Poll

↓

Transaction

↓

Process

↓

Commit Transaction

↓

Commit Offset
```

---

# Duplicate Processing

Suppose:

```text
Process Order

↓

Crash

↓

Restart
```

With At Least Once:

```text
Process Order Again
```

Applications should be prepared for duplicate deliveries.

---

# Idempotent Processing

To safely handle duplicates:

```text
Receive Event

↓

Check Already Processed?

↓

Yes

↓

Ignore

↓

No

↓

Process
```

Idempotent business logic is critical for At Least Once delivery.

---

# Real-World Examples

### At Most Once

```text
Application Logs
```

Missing a few log entries is acceptable.

---

### At Least Once

```text
Order Created

↓

Reserve Inventory

↓

Commit Offset
```

Duplicate processing is acceptable if the operation is idempotent.

---

### Exactly Once

```text
Transfer Money

↓

Update Ledger

↓

Commit Transaction
```

No duplicates or message loss are acceptable.

---

# Performance Comparison

```text
Fastest

↓

At Most Once

↓

At Least Once

↓

Exactly Once

↓

Strongest Reliability
```

Increasing reliability generally introduces additional coordination overhead.

---

# Common Misconceptions

### Exactly Once Does Not Mean

```text
Consumer Never Sees Duplicates
```

Exactly Once applies to **the complete processing pipeline**, not merely reading a message.

Applications must still be designed correctly.

---

# Choosing the Right Delivery Guarantee

| Application | Recommended Guarantee |
|-------------|-----------------------|
| Logging | At Most Once |
| Metrics | At Most Once |
| Order Processing | At Least Once |
| Inventory | At Least Once |
| Banking | Exactly Once |
| Payment Ledger | Exactly Once |
| Kafka Streams | Exactly Once |

---

# Best Practices

- Use At Least Once for most production applications.
- Design business logic to be idempotent.
- Use Manual Commit for reliable processing.
- Use Transactions only when business consistency requires them.
- Avoid Exactly Once unless its additional complexity is justified.
- Test failure scenarios regularly.

---

# Common Mistakes

- Assuming Auto Commit provides At Least Once guarantees.
- Believing Exactly Once eliminates all application concerns.
- Ignoring duplicate processing.
- Committing offsets before processing completes.
- Choosing Exactly Once for simple workloads where it adds unnecessary complexity.

---

# Summary

Delivery Semantics define how Kafka guarantees message processing in the presence of failures. At Most Once prioritizes speed but allows message loss. At Least Once guarantees that messages are not lost but may be processed more than once, making idempotent application logic essential. Exactly Once combines idempotent producers, transactions, and coordinated offset management to ensure that each message affects the system only once. Choosing the appropriate delivery guarantee depends on the application's reliability requirements, performance goals, and operational complexity.

---

# Key Takeaways

- Delivery Semantics determine how Kafka handles failures during message processing.
- Kafka supports At Most Once, At Least Once, and Exactly Once delivery.
- At Most Once may lose messages but never processes duplicates.
- At Least Once prevents message loss but may produce duplicate processing.
- Exactly Once eliminates both duplicates and message loss through transactions.
- Offset commit timing determines the delivery guarantee.
- Idempotent processing is essential for At Least Once delivery.
- Most production Kafka applications use At Least Once delivery because it offers the best balance between reliability and complexity.