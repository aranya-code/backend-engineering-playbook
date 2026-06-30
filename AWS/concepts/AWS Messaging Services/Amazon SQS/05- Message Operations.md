# Introduction

Applications communicate with Amazon SQS by performing **message operations**.

These operations allow producers to send messages and consumers to receive, process, update, and delete them.

Amazon SQS provides a set of APIs that enable reliable communication between distributed applications while maintaining durability and fault tolerance.

Understanding these operations is essential for designing scalable and resilient messaging systems.

---

# Message Operations Overview

The lifecycle of a message is controlled using a small set of APIs.

```
Producer

↓

SendMessage()

↓

Amazon SQS Queue

↓

ReceiveMessage()

↓

Process Message

↓

DeleteMessage()
```

Additional APIs are available for:

- Batch operations
- Extending visibility timeout
- Managing message metadata

---

# SendMessage

The `SendMessage()` API adds a message to an Amazon SQS queue.

After a successful request, the message becomes available for consumers.

---

## Workflow

```
Producer

↓

SendMessage()

↓

Amazon SQS Queue
```

---

## Required Parameters

| Parameter | Description |
|------------|-------------|
| Queue URL | Destination queue |
| Message Body | Data being sent |

---

## Optional Parameters

- DelaySeconds
- MessageAttributes
- MessageDeduplicationId (FIFO)
- MessageGroupId (FIFO)

---

## AWS CLI Example

```bash
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue \
  --message-body '{"orderId":101}'
```

---

## Boto3 Example

```python
import boto3

sqs = boto3.client("sqs")

response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody='{"orderId":101}'
)
```

---

# ReceiveMessage

Consumers retrieve messages using the `ReceiveMessage()` API.

Receiving a message does **not** delete it.

Instead, Amazon SQS temporarily hides it from other consumers.

---

## Workflow

```
Queue

↓

ReceiveMessage()

↓

Consumer

↓

Process Message
```

---

## Common Parameters

| Parameter | Description |
|------------|-------------|
| MaxNumberOfMessages | Maximum messages to retrieve (1–10) |
| VisibilityTimeout | Override queue visibility timeout |
| WaitTimeSeconds | Enable Long Polling |
| AttributeNames | Retrieve system attributes |
| MessageAttributeNames | Retrieve message attributes |

---

## AWS CLI Example

```bash
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue
```

---

## Boto3 Example

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=5
)
```

---

# DeleteMessage

A message is permanently removed only after the consumer calls `DeleteMessage()`.

If this API isn't called, the message will become available again after the Visibility Timeout expires.

---

## Workflow

```
Receive

↓

Process

↓

DeleteMessage()

↓

Message Removed
```

---

## Receipt Handle Required

Amazon SQS requires the **Receipt Handle**, not the Message ID, to delete a message.

---

## AWS CLI Example

```bash
aws sqs delete-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue \
  --receipt-handle RECEIPT_HANDLE
```

---

## Boto3 Example

```python
sqs.delete_message(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle
)
```

---

# ChangeMessageVisibility

Sometimes processing takes longer than expected.

Instead of allowing the message to become visible again, applications can extend the Visibility Timeout.

---

## Workflow

```
Receive

↓

Processing

↓

Need More Time

↓

ChangeMessageVisibility()

↓

Continue Processing

↓

Delete
```

---

## Example

Default timeout:

```
30 Seconds
```

Extended to:

```
5 Minutes
```

---

## AWS CLI Example

```bash
aws sqs change-message-visibility \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue \
  --receipt-handle RECEIPT_HANDLE \
  --visibility-timeout 300
```

---

## Boto3 Example

```python
sqs.change_message_visibility(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=300
)
```

---

# SendMessageBatch

Instead of sending one message at a time, Amazon SQS supports batch operations.

A single batch request can send up to **10 messages**.

---

## Benefits

- Fewer API calls
- Lower cost
- Better throughput
- Improved network efficiency

---

## Workflow

```
Application

↓

10 Messages

↓

SendMessageBatch()

↓

Amazon SQS
```

---

# DeleteMessageBatch

Deletes multiple messages in a single request.

Maximum:

```
10 Messages
```

---

## Workflow

```
Receive

↓

Process

↓

DeleteMessageBatch()

↓

Messages Removed
```

---

# ChangeMessageVisibilityBatch

Updates the Visibility Timeout for multiple messages simultaneously.

Useful for:

- Long-running batch jobs
- Parallel processing
- Worker pools

---

# Message Attributes

Message Attributes store additional application-specific metadata.

Unlike the message body, they are used to describe the message rather than contain the primary business data.

---

## Example

| Attribute | Value |
|-----------|-------|
| Priority | High |
| Department | Finance |
| Region | APAC |

---

## JSON Example

```text
Body:
{
    "orderId": 101
}

Attributes:

Priority = High

Region = APAC
```

---

## Supported Data Types

- String
- Number
- Binary

---

## Use Cases

- Message routing
- Logging
- Filtering
- Business metadata

---

# Message System Attributes

System attributes are managed by Amazon SQS.

Examples include:

- Message ID
- Sent Timestamp
- Approximate Receive Count
- Sender ID
- Approximate First Receive Timestamp

Applications typically read these values but do not modify them.

---

# Receipt Handle

The Receipt Handle is a temporary identifier generated when a consumer receives a message.

It is different from the Message ID.

---

## Example

```
Message ID

↓

12345

Receipt Handle

↓

AQEB123XYZ...
```

---

## Why Is It Needed?

Amazon SQS requires the Receipt Handle for:

- DeleteMessage()
- ChangeMessageVisibility()

Using the Message ID instead of the Receipt Handle results in an error.

---

# Idempotency Considerations

Amazon SQS Standard Queues provide **at-least-once delivery**.

This means a message may be delivered more than once.

Applications should therefore be idempotent.

---

## Example

```
Receive Message

↓

Process Payment

↓

Network Failure

↓

Receive Again
```

Without idempotency:

```
Customer Charged Twice
```

With idempotency:

```
Duplicate Ignored
```

---

## Common Strategies

- Database unique constraints
- Transaction IDs
- Deduplication tables
- Business identifiers

---

# AWS CLI Examples

## Send Message

```bash
aws sqs send-message \
  --queue-url QUEUE_URL \
  --message-body "Hello AWS"
```

---

## Receive Message

```bash
aws sqs receive-message \
  --queue-url QUEUE_URL
```

---

## Delete Message

```bash
aws sqs delete-message \
  --queue-url QUEUE_URL \
  --receipt-handle RECEIPT_HANDLE
```

---

# Boto3 Example

```python
import boto3

sqs = boto3.client("sqs")

# Send
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody="Hello AWS"
)

# Receive
response = sqs.receive_message(
    QueueUrl=QUEUE_URL
)

# Delete
receipt_handle = response["Messages"][0]["ReceiptHandle"]

sqs.delete_message(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle
)
```

---

# Best Practices

- Delete messages immediately after successful processing.
- Use batch APIs whenever possible.
- Always use the Receipt Handle for delete operations.
- Design consumers to be idempotent.
- Extend the Visibility Timeout for long-running tasks.
- Use Message Attributes instead of embedding metadata in the message body.
- Enable Long Polling to reduce unnecessary ReceiveMessage requests.

---

# Common Mistakes

## Using Message ID Instead of Receipt Handle

Only the Receipt Handle can delete a received message.

---

## Forgetting DeleteMessage()

Messages will be delivered again after the Visibility Timeout expires.

---

## Sending Large Payloads

Store large files in Amazon S3 and send only the object reference through SQS.

---

## Ignoring Batch APIs

Sending one message per request increases cost and reduces throughput.

---

## Assuming ReceiveMessage() Removes the Message

Receiving a message only makes it temporarily invisible.

The consumer must explicitly delete it after successful processing.

---

# Summary

Message operations are the core APIs used by producers and consumers to interact with Amazon SQS. By understanding how to send, receive, update visibility, and delete messages, developers can build reliable, fault-tolerant, and scalable asynchronous applications. Using batch operations, Receipt Handles, and idempotent consumers further improves performance and ensures correct message processing in distributed systems.