# Error Handling

## Overview

Failures are inevitable in distributed systems. Networks become unavailable, brokers restart, consumers crash, databases become unreachable, and applications may encounter invalid messages.

A robust Kafka consumer must be able to detect failures, recover gracefully, and continue processing without compromising data integrity.

Kafka provides several mechanisms to build fault-tolerant consumers, including:

- Retry mechanisms
- Manual Offset Management
- Dead Letter Topics (DLT)
- Exception handling
- Consumer recovery
- Delivery semantics
- Consumer rebalancing

Understanding these techniques is essential for building reliable event-driven systems.

---

# Why Error Handling Matters

Consider an Order Processing Service.

```text
Kafka

↓

Order Event

↓

Consumer

↓

Update Database
```

Suppose the database becomes unavailable.

Without error handling:

```text
Receive Message

↓

Database Error

↓

Consumer Crash
```

The application becomes unreliable.

With proper error handling:

```text
Receive Message

↓

Retry

↓

Database Available

↓

Process Successfully
```

The system recovers automatically.

---

# Types of Consumer Errors

Consumer failures generally fall into two categories.

```text
Recoverable Errors

↓

Temporary

-----------------------

Non-Recoverable Errors

↓

Permanent
```

Understanding the difference determines the recovery strategy.

---

# Recoverable Errors

These are temporary failures.

Examples include:

- Database unavailable
- Network interruption
- Broker restart
- Temporary timeout
- External API unavailable

Workflow:

```text
Receive Message

↓

Failure

↓

Retry

↓

Success
```

---

# Non-Recoverable Errors

These failures cannot be solved by retrying.

Examples:

- Invalid message format
- Corrupted data
- Deserialization failure
- Authentication failure
- Authorization failure
- Invalid business data

Workflow:

```text
Receive Message

↓

Failure

↓

Dead Letter Topic
```

Retries only waste resources.

---

# Consumer Error Handling Workflow

```text
Poll

↓

Receive Records

↓

Process Record

↓

Success?

↓

Yes

↓

Commit Offset

------------------------

No

↓

Recoverable?

↓

Yes

↓

Retry

↓

Success?

↓

Yes

↓

Commit

------------------------

No

↓

Dead Letter Topic
```

---

# Deserialization Errors

Consumers must deserialize bytes into application objects.

```text
Kafka Bytes

↓

Deserializer

↓

Application Object
```

Suppose the message contains invalid JSON.

```text
Deserializer

↓

Failure
```

Example:

```text
SerializationException
```

The message cannot be processed.

---

# Business Logic Errors

Suppose:

```text
Order Created

↓

Reserve Inventory

↓

Database Failure
```

The consumer should:

- Retry
- Avoid committing the offset
- Process again later

---

# Database Errors

Example:

```text
Consumer

↓

Insert Order

↓

Database Offline
```

Recovery:

```text
Retry

↓

Database Available

↓

Success
```

Most database failures are temporary.

---

# External API Failures

Example:

```text
Consumer

↓

Call Payment API

↓

Timeout
```

Instead of immediately failing:

```text
Retry

↓

Success
```

Retry with exponential backoff is commonly used.

---

# Retry Strategy

Basic retry flow:

```text
Attempt 1

↓

Failure

↓

Retry

↓

Attempt 2

↓

Failure

↓

Retry

↓

Success
```

Retries should be limited.

Unlimited retries may block partitions indefinitely.

---

# Exponential Backoff

Instead of retrying immediately:

```text
Retry

↓

1 Second

↓

2 Seconds

↓

4 Seconds

↓

8 Seconds
```

Benefits:

- Reduces pressure on downstream systems
- Prevents retry storms
- Improves recovery

---

# Poison Messages

Sometimes a message will never succeed.

Example:

```text
Invalid Customer ID

↓

Validation Failure
```

Retrying forever:

```text
Failure

↓

Retry

↓

Failure

↓

Retry
```

This blocks processing.

Such messages are called **Poison Messages**.

---

# Dead Letter Topic (DLT)

Instead of discarding poison messages:

```text
Consumer

↓

Failure

↓

Dead Letter Topic
```

Later:

```text
DLT Consumer

↓

Investigate

↓

Replay
```

Benefits:

- No data loss
- Easier debugging
- Safe production recovery

---

# Dead Letter Architecture

```text
Main Topic

↓

Consumer

↓

Failure

↓

Dead Letter Topic

↓

Operations Team

↓

Replay
```

This is a common enterprise architecture.

---

# Offset Handling During Errors

Correct sequence:

```text
Poll

↓

Process

↓

Success

↓

Commit Offset
```

Failure:

```text
Poll

↓

Process

↓

Failure

↓

No Commit
```

Kafka delivers the message again.

---

# Manual Commit During Errors

Manual Commit works naturally with retries.

```text
Failure

↓

No Commit

↓

Restart

↓

Read Same Record
```

No messages are lost.

---

# Error Handling with Rebalancing

Suppose:

```text
Consumer

↓

Crash
```

Kafka:

```text
Rebalance

↓

New Consumer

↓

Resume Processing
```

Processing continues from the last committed offset.

---

# Logging Errors

Every production consumer should log:

- Topic
- Partition
- Offset
- Exception
- Retry Count
- Processing Time

Example:

```text
Orders

Partition 2

Offset 850

Retry 3

Database Timeout
```

Detailed logs simplify troubleshooting.

---

# Monitoring Errors

Monitor:

- Retry Count
- Processing Failures
- Dead Letter Messages
- Commit Failures
- Consumer Lag
- Rebalance Count

Increasing error rates usually indicate:

- Infrastructure problems
- Application bugs
- Downstream failures

---

# Error Recovery Workflow

```text
Receive Record

↓

Process

↓

Failure

↓

Retry

↓

Failure

↓

Dead Letter Topic

↓

Manual Investigation

↓

Replay
```

This prevents both infinite retries and data loss.

---

# Circuit Breaker Pattern

Suppose a downstream service fails repeatedly.

Instead of:

```text
Retry Forever
```

Use:

```text
Failure

↓

Circuit Opens

↓

Skip Requests

↓

Recovery

↓

Circuit Closes
```

Benefits:

- Protects downstream systems
- Prevents cascading failures
- Improves application stability

---

# Idempotent Processing

Retries may cause duplicate deliveries.

Safe workflow:

```text
Receive Order

↓

Already Processed?

↓

Yes

↓

Ignore

↓

No

↓

Process
```

Idempotent business logic prevents duplicate side effects.

---

# Error Handling Architecture

```text
               Kafka Topic
                     │
                     ▼
               Consumer Poll
                     │
                     ▼
             Business Processing
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      Success               Failure
          │                     │
          ▼                     ▼
   Commit Offset          Retry Logic
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
               Success                Max Retries
                    │                       │
                    ▼                       ▼
             Commit Offset         Dead Letter Topic
```

---

# Real-World Example

An Order Service receives:

```text
Order Created
```

Processing:

```text
Reserve Inventory

↓

Payment Service

↓

Shipping
```

Payment API becomes unavailable.

Workflow:

```text
Retry

↓

Retry

↓

Retry

↓

Dead Letter Topic
```

Operations investigate the message later.

---

# Advantages

- Improved fault tolerance
- Automatic recovery
- No unnecessary message loss
- Better production stability
- Easier troubleshooting
- Supports reliable event processing

---

# Limitations

- More application complexity
- Retry logic requires careful design
- Dead Letter Topics require operational monitoring
- Idempotent processing is still required

---

# Best Practices

- Use Manual Commit for production consumers.
- Retry only recoverable errors.
- Implement exponential backoff.
- Use Dead Letter Topics for poison messages.
- Monitor retry rates and DLT growth.
- Keep business operations idempotent.
- Log sufficient information for debugging.
- Test failure scenarios regularly.

---

# Common Mistakes

- Retrying non-recoverable errors indefinitely.
- Committing offsets before processing completes.
- Ignoring poison messages.
- Not implementing Dead Letter Topics.
- Logging insufficient diagnostic information.
- Assuming retries alone guarantee reliability.

---

# Summary

Error handling is a fundamental aspect of building reliable Kafka consumers. By distinguishing between recoverable and non-recoverable failures, implementing controlled retry mechanisms, using Manual Offset Management, and routing poison messages to Dead Letter Topics, applications can recover from failures without compromising data integrity. Combined with idempotent processing, proper monitoring, and thoughtful retry strategies, these techniques enable resilient, production-ready Kafka consumer applications.

---

# Key Takeaways

- Consumer errors are classified as recoverable or non-recoverable.
- Manual Commit provides the safest recovery mechanism.
- Retry only temporary failures.
- Exponential backoff prevents retry storms.
- Dead Letter Topics isolate poison messages.
- Idempotent processing safely handles duplicate deliveries.
- Monitor retries, DLT growth, consumer lag, and processing failures.
- Robust error handling is essential for reliable event-driven systems.