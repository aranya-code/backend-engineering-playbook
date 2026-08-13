# FIFO, Dead Letter Queues & Message Lifecycle

> Learn how Amazon SQS guarantees message ordering, handles failed message processing, manages retries, and supports reliable distributed systems using FIFO queues, Dead Letter Queues (DLQs), Redrive Policies, deduplication, and message lifecycle management.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand FIFO queues
- Configure Message Groups
- Configure Deduplication
- Understand Dead Letter Queues (DLQs)
- Configure Redrive Policies
- Design retry mechanisms
- Build reliable message processing systems

---

# Why FIFO Queues?

Some workloads require strict ordering.

Examples:

- Banking transactions
- Payment processing
- Inventory updates
- Order fulfillment
- Financial systems

Incorrect ordering:

```text
Withdraw $100

↓

Deposit $100
```

could produce incorrect results.

FIFO queues preserve order.

---

# FIFO Queue Architecture

```text
Producer

↓

FIFO Queue

↓

Consumer

↓

Database
```

Messages are processed in the order they are sent.

---

# FIFO Queue Naming

FIFO queues must end with:

```text
.fifo
```

Example:

```text
payments.fifo
```

```text
inventory.fifo
```

---

# Create FIFO Queue

```bash
aws sqs create-queue \
--queue-name payments.fifo \
--attributes FifoQueue=true
```

---

# FIFO Characteristics

FIFO queues provide:

- Ordered delivery
- Exactly-once processing
- Message deduplication
- Message groups

---

# Message Groups

FIFO queues organize messages into groups.

Example:

```text
Payment A

↓

Payment B

↓

Payment C
```

All messages within the same group are processed sequentially.

---

# Multiple Message Groups

```text
Group A

↓

A1

↓

A2

↓

A3

────────────

Group B

↓

B1

↓

B2

↓

B3
```

Different groups can be processed simultaneously.

---

# Send FIFO Message

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body '{"payment":123}' \
--message-group-id payments
```

---

# Message Group Strategy

Good examples:

```text
customer-1001
```

```text
order-5002
```

```text
payment-group
```

Poor example:

```text
all-messages
```

Using a single group reduces throughput.

---

# Message Deduplication

Amazon SQS prevents duplicate messages.

Workflow:

```text
Producer

↓

Duplicate Message

↓

Ignored
```

---

# Deduplication ID

Explicit example:

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body '{"order":1}' \
--message-group-id orders \
--message-deduplication-id order-1
```

---

# Content-Based Deduplication

Amazon SQS can automatically generate deduplication IDs.

Create queue:

```bash
aws sqs create-queue \
--queue-name orders.fifo \
--attributes \
FifoQueue=true,ContentBasedDeduplication=true
```

---

# Deduplication Window

Duplicate messages are ignored for:

```text
5 Minutes
```

After five minutes, identical messages can be accepted again.

---

# Standard Queue Duplicates

Standard queues provide:

```text
At Least Once
```

delivery.

Applications must tolerate duplicate processing.

---

# Idempotent Consumers

Consumers should safely process duplicate messages.

Bad example:

```text
Charge Credit Card

↓

Twice
```

Good example:

```text
Already Processed?

↓

Yes

↓

Ignore
```

---

# Message Retry

If processing fails:

```text
Receive

↓

Process

↓

Failure

↓

Visibility Timeout

↓

Retry
```

Retries improve reliability.

---

# Retry Lifecycle

```text
Message

↓

Receive

↓

Failure

↓

Retry

↓

Success

↓

Delete
```

---

# Failed Processing

Without a Dead Letter Queue:

```text
Retry

↓

Retry

↓

Retry

↓

Forever
```

This can waste resources.

---

# Dead Letter Queue (DLQ)

A DLQ stores messages that repeatedly fail processing.

Architecture:

```text
Main Queue

↓

Failures

↓

Dead Letter Queue
```

---

# Why Use DLQs?

Benefits:

- Isolate bad messages
- Prevent infinite retries
- Simplify troubleshooting
- Improve system reliability

---

# Create Dead Letter Queue

```bash
aws sqs create-queue \
--queue-name orders-dlq
```

---

# Redrive Policy

A Redrive Policy moves failed messages to a DLQ.

Workflow:

```text
Main Queue

↓

Max Receives

↓

DLQ
```

---

# Max Receive Count

Example:

```text
5 Attempts

↓

Move to DLQ
```

The message will not be retried indefinitely.

---

# DLQ Architecture

```text
Producer

↓

Main Queue

↓

Consumer

↓

Success

↓

Delete

────────────

Failure

↓

Dead Letter Queue
```

---

# Inspect DLQ

Retrieve failed messages.

```bash
aws sqs receive-message \
--queue-url DLQ_URL
```

---

# Redrive Messages

Typical workflow:

```text
DLQ

↓

Fix Problem

↓

Move Back

↓

Main Queue
```

Messages can be reprocessed after the underlying issue is resolved.

---

# Message Retention

Messages remain available for:

```text
1 Minute

↓

14 Days
```

Longer retention provides more time for recovery.

---

# Message Expiration

After the retention period:

```text
Message

↓

Expired

↓

Deleted
```

Expired messages cannot be recovered.

---

# Message Size

Maximum size:

```text
256 KB
```

For larger payloads:

```text
Amazon S3

↓

Object Key

↓

Amazon SQS
```

---

# Queue Depth

Monitor:

```text
Messages Available

↓

Consumers

↓

Processing Rate
```

Growing queue depth often indicates insufficient consumers.

---

# CloudWatch Metrics

Important metrics:

- ApproximateNumberOfMessagesVisible
- ApproximateAgeOfOldestMessage
- NumberOfMessagesSent
- NumberOfMessagesDeleted
- NumberOfMessagesReceived

---

# FIFO vs Standard

| Feature | Standard | FIFO |
|----------|----------|------|
| Ordering | Best Effort | Guaranteed |
| Delivery | At Least Once | Exactly Once |
| Deduplication | No | Yes |
| Message Groups | No | Yes |
| Throughput | Very High | Lower |

---

# Common Errors

## Missing MessageGroupId

FIFO queues require:

```text
MessageGroupId
```

for every message.

---

## Duplicate Message Ignored

Possible causes:

- Duplicate Deduplication ID
- Content-Based Deduplication

---

## Queue Name Invalid

FIFO queues must end with:

```text
.fifo
```

---

## DLQ Growing Rapidly

Possible causes:

- Consumer bug
- Invalid message format
- Database failure
- External API failure

Investigate before replaying messages.

---

# Production Best Practices

- Use FIFO only when ordering is required.
- Design consumers to be idempotent.
- Configure Dead Letter Queues for every production queue.
- Set appropriate Max Receive Count values.
- Monitor DLQ size continuously.
- Keep Message Groups balanced.
- Avoid a single Message Group for all traffic.
- Investigate failed messages before replaying them.
- Store large payloads in Amazon S3 instead of SQS.

---

# Real-World Workflow

```text
Backend API

↓

Amazon SQS

↓

Worker

↓

Database

↓

Delete

────────────

Failure

↓

Dead Letter Queue

↓

Operations Team

↓

Replay
```

---

# Architecture Note

```text
Producer
      │
      ▼
Amazon SQS FIFO
      │
      ├── Message Group
      ├── Deduplication
      ├── Visibility Timeout
      └── Dead Letter Queue
              │
              ▼
Consumer
```

A production FIFO queue combines message ordering, deduplication, retries, and Dead Letter Queues to provide reliable message processing while preventing duplicate work and isolating failures.

---

# Interview Note

### Question

**What is a Dead Letter Queue (DLQ), and why is it important in Amazon SQS?**

### Answer

A Dead Letter Queue (DLQ) is a separate Amazon SQS queue that stores messages that cannot be successfully processed after a configured number of retry attempts. A Redrive Policy moves these failed messages to the DLQ once the **Maximum Receive Count** is exceeded. DLQs prevent infinite processing loops, isolate problematic messages, simplify troubleshooting, and improve the reliability of distributed systems.

---

# Key Takeaways

- FIFO queues guarantee message ordering and exactly-once processing.
- Message Groups allow ordered processing while enabling parallelism across groups.
- Deduplication prevents duplicate messages from being processed.
- Dead Letter Queues isolate failed messages after repeated processing failures.
- Redrive Policies define when messages are moved to a DLQ.
- Consumers should always be idempotent, even when using FIFO queues.
- Monitoring queue depth and DLQ size is essential for maintaining healthy production messaging systems.