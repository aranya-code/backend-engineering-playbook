# Delivery Guarantees

## Overview

One of the most important questions in any messaging system is:

> **What happens if something fails while sending or processing a message?**

For example:

- What if the producer crashes after sending a message?
- What if the broker crashes before saving it?
- What if the consumer crashes after processing but before committing the offset?
- Can a message be lost?
- Can a message be processed twice?

Apache Kafka addresses these questions through **Delivery Guarantees**, which define how reliably messages are delivered from producers to consumers.

Kafka supports three delivery guarantees:

- At Most Once
- At Least Once
- Exactly Once

Each guarantee offers a different balance between **performance**, **reliability**, and **complexity**.

Choosing the appropriate guarantee depends on the application's business requirements.

---

# Why Delivery Guarantees Matter

Imagine a banking application.

```text
Transfer ₹10,000
```

If the message is:

- Lost → Money disappears.
- Processed twice → Customer is charged twice.
- Processed exactly once → Correct behavior.

Clearly, different applications have different reliability requirements.

Examples:

| Application | Requirement |
|--------------|-------------|
| Log Collection | Losing a few logs may be acceptable |
| Social Media Likes | Duplicate likes are undesirable but manageable |
| Payment System | Neither loss nor duplication is acceptable |
| Banking | Exactly once processing is essential |

---

# Message Lifecycle

A message passes through several stages.

```text
Producer

↓

Kafka Broker

↓

Consumer

↓

Business Logic

↓

Offset Commit
```

Failures can occur at any stage.

Delivery guarantees define how Kafka behaves during these failures.

---

# At Most Once

## Definition

A message is delivered **zero or one time**.

It may be lost.

It is **never delivered twice**.

---

## Workflow

```text
Producer

↓

Kafka

↓

Consumer

↓

Commit Offset

↓

Process Message
```

Notice that the offset is committed **before** the message is processed.

---

## Failure Scenario

Suppose the consumer crashes immediately after committing the offset.

```text
Read Message

↓

Commit Offset

↓

Crash
```

After restarting:

```text
Consumer

↓

Starts From Next Offset
```

The previous message is skipped forever.

It has been lost.

---

## Characteristics

Advantages:

- Fastest processing
- No duplicate messages
- Simple implementation

Disadvantages:

- Messages may be permanently lost

---

## Typical Use Cases

Suitable for:

- Metrics collection
- Monitoring dashboards
- Temporary cache updates
- Non-critical logging

Where occasional message loss is acceptable.

---

# At Least Once

## Definition

A message is delivered **one or more times**.

It is **never lost**.

Duplicates are possible.

---

## Workflow

```text
Producer

↓

Kafka

↓

Consumer

↓

Process Message

↓

Commit Offset
```

The offset is committed **after** successful processing.

---

## Failure Scenario

Suppose the consumer crashes after processing but before committing.

```text
Read Message

↓

Process Message

↓

Crash
```

Kafka still believes the message has not been processed.

After restart:

```text
Consumer

↓

Reads Same Message Again
```

The message is processed twice.

---

## Characteristics

Advantages:

- No message loss
- Simple to implement
- Common production choice

Disadvantages:

- Duplicate processing is possible

Applications must therefore be **idempotent**.

---

## Example

```text
Inventory Updated

↓

Crash

↓

Inventory Updated Again
```

If the update is not idempotent:

```text
100 Items

↓

99 Items

↓

98 Items
```

Inventory becomes incorrect.

Proper application logic prevents this.

---

## Typical Use Cases

- Order Processing
- Notifications
- Inventory Management
- Event Processing
- Analytics Pipelines

Most Kafka applications use **At Least Once**.

---

# Exactly Once

## Definition

A message is processed **exactly one time**.

No loss.

No duplicates.

---

## Workflow

```text
Producer

↓

Kafka

↓

Consumer

↓

Transaction

↓

Commit Offset

↓

Complete
```

Kafka coordinates producers, brokers, and consumers to guarantee correctness.

---

# How Kafka Achieves Exactly Once

Kafka combines several features.

- Idempotent Producer
- Transactions
- Transaction Coordinator
- Offset Commit inside Transactions

Together they ensure:

```text
Processed Once

Only Once
```

Even if failures occur.

---

# Example

Payment processing.

```text
Debit Account

↓

Credit Merchant

↓

Commit Offset
```

If any step fails:

```text
Rollback Transaction
```

The message is safely retried without duplicates.

---

# Characteristics

Advantages:

- No duplicates
- No message loss
- Highest reliability

Disadvantages:

- Most complex configuration
- Slightly lower throughput
- Higher latency

---

# Delivery Guarantee Comparison

| Feature | At Most Once | At Least Once | Exactly Once |
|----------|--------------|---------------|---------------|
| Message Loss | Possible | No | No |
| Duplicate Messages | No | Possible | No |
| Performance | Highest | High | Moderate |
| Complexity | Low | Medium | High |
| Production Usage | Limited | Very Common | Critical Systems |

---

# Visual Comparison

## At Most Once

```text
Read

↓

Commit Offset

↓

Process

↓

Crash

❌ Message Lost
```

---

## At Least Once

```text
Read

↓

Process

↓

Crash

↓

Read Again

⚠ Duplicate
```

---

## Exactly Once

```text
Read

↓

Transaction

↓

Commit

↓

Success

✅ One Processing
```

---

# Producer Perspective

Delivery guarantees begin at the producer.

Reliable producer configuration:

```properties
acks=all
enable.idempotence=true
retries=Integer.MAX_VALUE
```

These settings reduce message loss and prevent duplicate writes.

---

# Consumer Perspective

Consumers influence delivery guarantees through offset management.

Auto Commit:

```properties
enable.auto.commit=true
```

Often results in:

```text
At Most Once
```

Manual Commit:

```text
Read

↓

Process

↓

Commit Offset
```

Provides:

```text
At Least Once
```

---

# Exactly Once Requirements

To achieve Exactly Once processing:

- Idempotent Producer
- Transactions
- Manual Offset Management
- Transaction-aware Consumer
- Reliable Storage

Missing any of these may reduce the guarantee to At Least Once.

---

# Which Guarantee Should You Choose?

| Scenario | Recommendation |
|-----------|----------------|
| Logging | At Most Once |
| Monitoring | At Most Once |
| Notifications | At Least Once |
| Inventory | At Least Once |
| Order Processing | At Least Once |
| Banking | Exactly Once |
| Financial Transactions | Exactly Once |
| Payment Systems | Exactly Once |

---

# Best Practices

- Use **At Least Once** for most business applications.
- Use **Exactly Once** only when duplicate processing is unacceptable.
- Make consumers idempotent whenever possible.
- Commit offsets only after successful processing.
- Enable idempotent producers in production.
- Monitor retry rates and transaction failures.

---

# Common Mistakes

- Assuming Kafka automatically provides Exactly Once semantics.
- Using auto-commit for critical business workflows.
- Ignoring duplicate message handling.
- Forgetting to make consumers idempotent.
- Using Exactly Once where At Least Once is sufficient, adding unnecessary complexity.

---

# Summary

Delivery guarantees define how reliably Kafka delivers messages between producers and consumers. At Most Once prioritizes performance but may lose messages. At Least Once ensures messages are not lost but may process them more than once. Exactly Once combines idempotent producers, transactions, and careful offset management to ensure each message is processed only once. Choosing the right delivery guarantee depends on the application's reliability requirements and acceptable trade-offs.

---

# Key Takeaways

- Kafka supports three delivery guarantees: At Most Once, At Least Once, and Exactly Once.
- At Most Once prioritizes speed but may lose messages.
- At Least Once prevents message loss but may produce duplicates.
- Exactly Once guarantees no message loss and no duplicate processing.
- Producer acknowledgements, retries, and idempotency influence delivery guarantees.
- Consumer offset management plays a critical role in reliable message processing.
- Most production applications use At Least Once processing with idempotent consumers.
- Exactly Once is typically reserved for financial and other mission-critical systems.