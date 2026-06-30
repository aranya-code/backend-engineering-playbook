# Introduction

Amazon SQS provides **two queue types**, each designed for different business requirements.

Choosing the correct queue type is one of the most important architectural decisions when designing distributed systems.

The two queue types are:

- Standard Queue
- FIFO (First-In-First-Out) Queue

Although both queues perform the same basic task—storing messages until they are processed—they differ significantly in message ordering, delivery guarantees, throughput, and duplicate handling.

---

# Standard Queue

A **Standard Queue** is the default queue type in Amazon SQS.

It is designed for applications that require:

- High throughput
- Low latency
- Maximum scalability

Ordering is **not guaranteed**, and duplicate messages are possible.

---

## Characteristics

- Unlimited throughput
- At-least-once delivery
- Best-effort ordering
- Very low latency
- Highly scalable
- Supports multiple producers and consumers

---

## Architecture

```
                 Producer A
                     │
                     │
                 Producer B
                     │
                     ▼
              ┌──────────────┐
              │ Standard SQS │
              └──────────────┘
               ▲     ▲      ▲
               │     │      │
          Consumer1 Consumer2 Consumer3
```

Messages are distributed across multiple servers.

This distribution enables Amazon SQS to achieve virtually unlimited throughput.

---

## Delivery Guarantee

Standard Queue guarantees

```
At-Least-Once Delivery
```

This means:

Every message will be delivered **at least once**.

However,

the same message may occasionally be delivered more than once.

Example

```
Producer

↓

Message #101

↓

Consumer

↓

Network Failure

↓

Amazon SQS

↓

Consumer Receives Again
```

Applications must therefore be **idempotent**.

---

# Best-Effort Ordering

Standard queues attempt to preserve message order.

However,

under heavy load or distributed processing,

messages may arrive in a different order.

Example

Producer sends

```
1

2

3

4

5
```

Consumer may receive

```
1

3

2

5

4
```

Ordering is **not guaranteed**.

---

# Duplicate Messages

Duplicate messages are normal behavior in Standard Queues.

Example

```
Producer

↓

Message A

↓

Consumer

↓

Network Failure

↓

Amazon SQS

↓

Message A Again
```

Applications should be designed to safely ignore duplicates.

---

# When Should You Use Standard Queue?

Use Standard Queue when:

- Maximum throughput is required.
- Ordering is not important.
- Duplicate processing is acceptable.
- Consumers are idempotent.

---

## Common Use Cases

- Log processing
- Image processing
- Video transcoding
- Analytics
- Batch processing
- Email generation
- Background jobs

---

# FIFO Queue

FIFO stands for

```
First In First Out
```

FIFO queues guarantee that messages are processed **in the exact order they are sent**.

FIFO queues are designed for applications where message order and duplicate prevention are critical.

---

## Characteristics

- Ordered processing
- Exactly-once processing (within the deduplication window)
- Message deduplication
- Lower throughput than Standard Queue
- Message groups supported

---

## Architecture

```
              Producer

                 │

                 ▼

          ┌────────────┐
          │ FIFO Queue │
          └────────────┘

                 │

                 ▼

             Consumer

1

↓

2

↓

3

↓

4

↓

5
```

Every message is processed sequentially.

---

# Ordered Delivery

Suppose a producer sends:

```
Order Created

↓

Payment Processed

↓

Inventory Updated

↓

Shipping Started
```

FIFO guarantees

```
Order Created

↓

Payment Processed

↓

Inventory Updated

↓

Shipping Started
```

This order will never change.

---

# Why Ordering Matters

Consider a banking application.

Incorrect ordering:

```
Withdraw ₹1000

↓

Deposit ₹500
```

If these arrive as

```
Deposit ₹500

↓

Withdraw ₹1000
```

the account balance becomes incorrect.

FIFO prevents this issue.

---

# Message Groups

FIFO queues introduce the concept of **Message Groups**.

Messages in the same group are processed sequentially.

Messages in different groups can be processed in parallel.

Example

```
Group A

1

↓

2

↓

3

↓

4

----------------

Group B

1

↓

2

↓

3
```

This improves throughput while preserving order within each group.

---

# Message Deduplication

FIFO queues automatically detect duplicate messages.

Amazon SQS uses either:

- Explicit Deduplication ID
- Content-Based Deduplication

Duplicate messages sent within the deduplication interval are ignored.

Example

```
Producer

↓

Message ID = ABC123

↓

Producer Sends Again

↓

Same ID

↓

Ignored
```

---

# Content-Based Deduplication

Instead of providing a Deduplication ID,

Amazon SQS can generate one automatically using the message body.

Example

```
{
   "orderId":105
}
```

Sending the same payload again results in only one stored message.

---

# FIFO Throughput

FIFO queues provide lower throughput than Standard queues because ordering must be maintained.

AWS offers:

- Classic FIFO throughput
- High Throughput FIFO mode

High Throughput FIFO significantly increases processing capacity while maintaining ordering guarantees.

---

# Standard vs FIFO

| Feature | Standard Queue | FIFO Queue |
|----------|---------------|------------|
| Ordering | Best Effort | Guaranteed |
| Delivery | At Least Once | Exactly Once* |
| Duplicate Messages | Possible | Eliminated (within deduplication window) |
| Throughput | Virtually Unlimited | Lower (Higher with High Throughput FIFO) |
| Latency | Very Low | Slightly Higher |
| Message Groups | No | Yes |
| Deduplication | No | Yes |
| Best For | High-scale workloads | Ordered business transactions |

> *Exactly-once processing depends on proper use of deduplication IDs and application design.

---

# Decision Guide

```
Do you need strict ordering?

│

├── Yes

│      │

│      └── FIFO Queue

│

└── No

       │

       └── Standard Queue
```

---

# Choosing the Right Queue

Choose **Standard Queue** when:

- Performance is the highest priority.
- Millions of messages must be processed.
- Ordering is not required.
- Duplicate processing is acceptable.

Examples:

- Image resizing
- Log ingestion
- Background jobs
- Notifications
- Email processing

---

Choose **FIFO Queue** when:

- Ordering must be preserved.
- Duplicate processing cannot be tolerated.
- Business transactions require consistency.

Examples:

- Banking
- Payment processing
- Order management
- Inventory systems
- Financial trading
- Ticket booking systems

---

# Real-World Example 1 – Image Processing

```
Users

↓

Upload Images

↓

Standard Queue

↓

100 Workers

↓

Resize Images
```

Image processing is independent.

Ordering does not matter.

Use **Standard Queue**.

---

# Real-World Example 2 – Payment Processing

```
Order Created

↓

FIFO Queue

↓

Payment

↓

Inventory

↓

Shipping
```

Order is critical.

Use **FIFO Queue**.

---

# Real-World Example 3 – Banking

```
Deposit

↓

Withdraw

↓

Balance Update
```

Transactions must execute in sequence.

FIFO Queue is the correct choice.

---

# Best Practices

- Use **Standard Queue** unless strict ordering is required.
- Design consumers to be **idempotent**, especially with Standard Queues.
- Use **FIFO Queue** only when ordering or duplicate prevention is essential.
- Use **Message Groups** to improve FIFO throughput.
- Enable **Content-Based Deduplication** when appropriate.
- Monitor throughput and queue depth with Amazon CloudWatch.

---

# Common Mistakes

### Choosing FIFO for Every Workload

FIFO introduces additional overhead.

If ordering isn't required, use Standard Queue.

---

### Assuming Standard Queue Preserves Order

Standard Queue provides **best-effort ordering**, not guaranteed ordering.

---

### Ignoring Duplicate Messages

Applications using Standard Queues must handle duplicate deliveries safely.

---

### Using a Single Message Group

Using one message group in a FIFO queue limits parallelism.

Use multiple message groups where possible to improve throughput while maintaining order within each group.

---

# Key Takeaways

- Amazon SQS offers **Standard** and **FIFO** queue types.
- **Standard Queues** prioritize scalability and throughput, using at-least-once delivery and best-effort ordering.
- **FIFO Queues** prioritize message order and duplicate prevention using deduplication and message groups.
- The choice between Standard and FIFO should be based on business requirements rather than preference.

---

# Summary

Selecting the appropriate queue type is fundamental to designing reliable distributed systems.

Use **Standard Queues** for high-throughput, scalable workloads where occasional duplicate messages and out-of-order delivery are acceptable.

Use **FIFO Queues** when message ordering and exactly-once processing are business-critical, such as financial transactions, inventory management, or order processing.