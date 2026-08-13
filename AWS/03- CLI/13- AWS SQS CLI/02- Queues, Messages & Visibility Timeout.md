# Queues, Messages & Visibility Timeout

> Learn how Amazon SQS stores, delivers, and manages messages using the AWS CLI. This chapter covers queue attributes, sending and receiving messages, message visibility, long polling, delay queues, message retention, batching, and production message processing strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Send and receive messages
- Understand the message lifecycle
- Configure Visibility Timeout
- Configure Long Polling
- Configure Delay Queues
- Configure Message Retention
- Process messages efficiently
- Build reliable message consumers

---

# Queue Attributes

Every Amazon SQS queue has configurable attributes.

Examples include:

- Visibility Timeout
- Message Retention
- Delay Seconds
- Maximum Message Size
- Receive Wait Time
- Dead Letter Queue
- Encryption

View attributes:

```bash
aws sqs get-queue-attributes \
--queue-url QUEUE_URL \
--attribute-names All
```

---

# Message Lifecycle

A message follows this lifecycle.

```text
Producer

↓

Queue

↓

Consumer Receives

↓

Visibility Timeout

↓

Delete Message
```

If the message is not deleted:

```text
Visibility Timeout Ends

↓

Message Reappears
```

---

# Sending Messages

Send a message.

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body "Hello World"
```

---

# Send JSON Message

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body '{"orderId":12345,"status":"created"}'
```

---

# Send FIFO Message

FIFO queues require:

- Message Group ID
- (Optional) Deduplication ID

Example:

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body '{"payment":"completed"}' \
--message-group-id payments
```

---

# Message Attributes

Messages can include metadata.

Example:

```text
Message

│

├── Body

├── Attributes

└── Timestamp
```

Useful metadata:

- Order Type
- Customer ID
- Priority
- Event Type

---

# Receive Messages

Retrieve messages.

```bash
aws sqs receive-message \
--queue-url QUEUE_URL
```

---

# Receive Multiple Messages

Receive up to 10 messages.

```bash
aws sqs receive-message \
--queue-url QUEUE_URL \
--max-number-of-messages 10
```

---

# Message Processing Workflow

```text
Receive

↓

Process

↓

Delete
```

Never delete a message before successful processing.

---

# Delete Message

Every received message contains a:

```text
Receipt Handle
```

Delete using:

```bash
aws sqs delete-message \
--queue-url QUEUE_URL \
--receipt-handle RECEIPT_HANDLE
```

---

# Why Receipt Handles?

Messages are deleted using Receipt Handles instead of Message IDs.

```text
Message ID

↓

Identification

────────────

Receipt Handle

↓

Deletion
```

Receipt Handles change every time a message is received.

---

# Visibility Timeout

After a consumer receives a message:

```text
Consumer

↓

Message Hidden

↓

Visibility Timeout

↓

Delete
```

Other consumers cannot see the message during this period.

---

# Example

Visibility Timeout:

```text
30 Seconds
```

Consumer finishes processing:

```text
10 Seconds
```

Deletes message:

```text
Completed
```

Message never becomes visible again.

---

# Consumer Failure

If the consumer crashes:

```text
Receive

↓

Crash

↓

Visibility Timeout Ends

↓

Message Returns
```

Another worker can process it.

---

# Change Visibility Timeout

Increase timeout while processing.

```bash
aws sqs change-message-visibility \
--queue-url QUEUE_URL \
--receipt-handle RECEIPT_HANDLE \
--visibility-timeout 300
```

---

# Queue Visibility Timeout

Default timeout can be configured.

```bash
aws sqs set-queue-attributes \
--queue-url QUEUE_URL \
--attributes VisibilityTimeout=60
```

---

# Choosing Visibility Timeout

Recommended:

```text
Visibility Timeout

>

Maximum Processing Time
```

Example:

| Processing Time | Visibility Timeout |
|-----------------|--------------------|
| 10 sec | 30 sec |
| 1 min | 3 min |
| 5 min | 10 min |

---

# Long Polling

Without Long Polling:

```text
Consumer

↓

Poll

↓

No Messages

↓

Empty Response
```

Repeated polling wastes API calls.

---

# Long Polling Workflow

```text
Consumer

↓

Wait

↓

Message Arrives

↓

Receive
```

Benefits:

- Fewer API requests
- Lower cost
- Faster message retrieval

---

# Enable Long Polling

```bash
aws sqs set-queue-attributes \
--queue-url QUEUE_URL \
--attributes ReceiveMessageWaitTimeSeconds=20
```

Maximum:

```text
20 Seconds
```

---

# Receive Using Long Polling

```bash
aws sqs receive-message \
--queue-url QUEUE_URL \
--wait-time-seconds 20
```

---

# Short Polling vs Long Polling

| Feature | Short Polling | Long Polling |
|----------|---------------|--------------|
| Wait Time | Immediate | Up to 20 sec |
| Empty Responses | Many | Few |
| Cost | Higher | Lower |
| Recommendation | Rarely | Production |

---

# Delay Queues

Delay Queues postpone message availability.

```text
Producer

↓

Queue

↓

Delay

↓

Consumer
```

Useful for:

- Retry logic
- Scheduled processing
- Buffering workloads

---

# Configure Queue Delay

```bash
aws sqs set-queue-attributes \
--queue-url QUEUE_URL \
--attributes DelaySeconds=30
```

---

# Per-Message Delay

```bash
aws sqs send-message \
--queue-url QUEUE_URL \
--message-body "Reminder" \
--delay-seconds 60
```

---

# Message Retention

Messages remain in the queue for:

```text
1 Minute

↓

14 Days
```

Default:

```text
4 Days
```

---

# Configure Message Retention

```bash
aws sqs set-queue-attributes \
--queue-url QUEUE_URL \
--attributes MessageRetentionPeriod=345600
```

Example:

```text
345600 seconds

↓

4 Days
```

---

# Maximum Message Size

Amazon SQS supports messages up to:

```text
256 KB
```

For larger payloads:

```text
Amazon S3

↓

Store Object

↓

Send Object Key via SQS
```

---

# Batch Operations

Batch processing improves efficiency.

Maximum:

```text
10 Messages
```

---

# Send Batch

```bash
aws sqs send-message-batch
```

---

# Delete Batch

```bash
aws sqs delete-message-batch
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

A growing queue usually indicates insufficient consumers.

---

# Message Ordering

Standard Queue:

```text
A

↓

C

↓

B
```

Ordering is not guaranteed.

FIFO Queue:

```text
A

↓

B

↓

C
```

Ordering is guaranteed within a Message Group.

---

# Common Errors

## QueueDoesNotExist

Verify:

- Queue URL
- Region
- AWS Account

---

## ReceiptHandleIsInvalid

Verify:

- Latest Receipt Handle
- Message not already deleted

---

## InvalidMessageContents

Verify:

- UTF-8 encoding
- Message size
- Valid JSON (if applicable)

---

## Visibility Timeout Too Short

Symptoms:

- Duplicate processing
- Same message received repeatedly

Increase Visibility Timeout.

---

# Production Best Practices

- Enable Long Polling.
- Set Visibility Timeout longer than processing time.
- Delete messages only after successful processing.
- Process messages idempotently.
- Use batch operations for higher throughput.
- Keep message payloads small.
- Store large objects in Amazon S3.
- Monitor queue depth using CloudWatch.
- Design consumers to handle duplicate deliveries.

---

# Real-World Workflow

```text
API

↓

Amazon SQS

↓

Worker

↓

Amazon RDS

↓

Delete Message
```

---

# Architecture Note

```text
Producer
      │
      ▼
Amazon SQS
      │
      ▼
Consumer
      │
      ├── Process Message
      ├── Delete Message
      └── Retry on Failure
```

A reliable SQS consumer retrieves messages, processes them successfully, deletes them using the Receipt Handle, and relies on Visibility Timeout to prevent duplicate concurrent processing.

---

# Interview Note

### Question

**What is Visibility Timeout in Amazon SQS?**

### Answer

Visibility Timeout is the period during which a received message becomes temporarily invisible to other consumers after being retrieved from an Amazon SQS queue. It prevents multiple consumers from processing the same message simultaneously. If the consumer successfully processes the message, it deletes it before the timeout expires. If the consumer fails or crashes, the message becomes visible again after the timeout, allowing another consumer to process it.

---

# Key Takeaways

- Messages are deleted using Receipt Handles, not Message IDs.
- Visibility Timeout prevents concurrent processing of the same message.
- Long Polling reduces empty responses and API costs.
- Delay Queues postpone message delivery.
- Message Retention controls how long messages remain in the queue.
- Batch operations improve throughput and reduce API calls.
- Production consumers should be idempotent and always delete messages only after successful processing.