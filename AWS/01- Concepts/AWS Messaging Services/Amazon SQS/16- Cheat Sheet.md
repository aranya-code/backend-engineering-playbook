# Introduction

This chapter serves as a quick reference for Amazon SQS concepts, limits, AWS CLI commands, and best practices.

Use it as a last-minute revision guide before interviews or while working with Amazon SQS in production.

---

# Amazon SQS at a Glance

| Feature | Value |
|----------|-------|
| Service Type | Fully Managed Message Queue |
| Communication Style | Asynchronous |
| Queue Types | Standard, FIFO |
| Maximum Message Size | 256 KB |
| Message Retention | 1 Minute – 14 Days |
| Default Message Retention | 4 Days |
| Default Visibility Timeout | 30 Seconds |
| Maximum Visibility Timeout | 12 Hours |
| Maximum Delay Queue | 15 Minutes |
| Maximum Long Polling | 20 Seconds |
| Batch Size | 10 Messages |
| Encryption | AWS KMS |
| Monitoring | Amazon CloudWatch |
| Audit Logs | AWS CloudTrail |

---

# Standard Queue

### Features

- Virtually unlimited throughput
- At-least-once delivery
- Best-effort ordering
- Duplicate messages possible

### Best For

- Background jobs
- Image processing
- Log processing
- Analytics
- Event-driven systems

---

# FIFO Queue

### Features

- First-In-First-Out ordering
- Exactly-once processing (within the deduplication window)
- Message deduplication
- Message groups

### Best For

- Payment systems
- Banking
- Order processing
- Inventory management

---

# Message Lifecycle

```
Producer

↓

SendMessage()

↓

Amazon SQS

↓

ReceiveMessage()

↓

Visibility Timeout

↓

Process

↓

DeleteMessage()
```

---

# Important APIs

| API | Purpose |
|------|---------|
| SendMessage() | Send one message |
| SendMessageBatch() | Send multiple messages |
| ReceiveMessage() | Receive messages |
| DeleteMessage() | Delete a processed message |
| DeleteMessageBatch() | Delete multiple messages |
| ChangeMessageVisibility() | Extend visibility timeout |
| PurgeQueue() | Remove all messages |

---

# Queue Attributes

| Attribute | Purpose |
|-----------|----------|
| Visibility Timeout | Prevent duplicate processing |
| Message Retention | Store messages |
| Delay Queue | Delay message delivery |
| Long Polling | Reduce empty receives |
| Redrive Policy | Configure DLQ |
| SSE | Encrypt messages |
| Tags | Organize resources |

---

# Visibility Timeout

| Property | Value |
|----------|-------|
| Default | 30 Seconds |
| Maximum | 12 Hours |

Remember

```
Receive

↓

Invisible

↓

Delete
```

---

# Delay Queue

| Property | Value |
|----------|-------|
| Default | 0 Seconds |
| Maximum | 15 Minutes |

Purpose

```
Send

↓

Wait

↓

Receive
```

---

# Long Polling

| Property | Value |
|----------|-------|
| Default | 0 Seconds |
| Maximum | 20 Seconds |

Recommended

```
20 Seconds
```

Benefits

- Lower cost
- Fewer API calls
- Better performance

---

# Dead Letter Queue

Purpose

```
Retry

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Configuration

- Dead Letter Queue ARN
- Maximum Receive Count

---

# Security Checklist

- IAM Policies
- Queue Policies
- HTTPS
- AWS KMS
- CloudTrail
- CloudWatch

Always follow the Principle of Least Privilege.

---

# Monitoring Metrics

| CloudWatch Metric | Purpose |
|-------------------|----------|
| ApproximateNumberOfMessagesVisible | Messages waiting |
| ApproximateNumberOfMessagesNotVisible | Messages being processed |
| ApproximateAgeOfOldestMessage | Queue delay |
| NumberOfMessagesSent | Incoming workload |
| NumberOfMessagesReceived | Consumer activity |
| NumberOfMessagesDeleted | Successful processing |
| NumberOfEmptyReceives | Empty polling requests |

---

# AWS CLI Commands

## Create Queue

```bash
aws sqs create-queue \
    --queue-name order-queue
```

---

## List Queues

```bash
aws sqs list-queues
```

---

## Send Message

```bash
aws sqs send-message \
    --queue-url QUEUE_URL \
    --message-body "Hello World"
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

## Purge Queue

```bash
aws sqs purge-queue \
    --queue-url QUEUE_URL
```

---

## Delete Queue

```bash
aws sqs delete-queue \
    --queue-url QUEUE_URL
```

---

# Boto3 Quick Reference

## Create Client

```python
import boto3

sqs = boto3.client("sqs")
```

---

## Send Message

```python
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody="Hello World"
)
```

---

## Receive Message

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=20
)
```

---

## Delete Message

```python
sqs.delete_message(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle
)
```

---

# Common Limits

| Resource | Limit |
|----------|-------|
| Message Size | 256 KB |
| Batch Size | 10 Messages |
| Long Polling | 20 Seconds |
| Delay Queue | 15 Minutes |
| Visibility Timeout | 12 Hours |
| Message Retention | 14 Days |

---

# Best Practices Checklist

| Practice | Recommended |
|----------|-------------|
| Use Long Polling | ✅ |
| Configure DLQ | ✅ |
| Enable Encryption | ✅ |
| Design Idempotent Consumers | ✅ |
| Monitor CloudWatch Metrics | ✅ |
| Delete Messages After Processing | ✅ |
| Use Batch APIs | ✅ |
| Use IAM Roles | ✅ |
| Store Large Files in S3 | ✅ |
| Use Infrastructure as Code | ✅ |

---

# Common Mistakes

❌ Forgetting `DeleteMessage()`

❌ Visibility Timeout too short

❌ No Dead Letter Queue

❌ Using FIFO unnecessarily

❌ Sending files larger than 256 KB

❌ Ignoring CloudWatch metrics

❌ Overly permissive IAM policies

❌ Disabling Long Polling

---

# Interview Quick Facts

| Question | Answer |
|----------|--------|
| Queue Types | Standard and FIFO |
| Default Visibility Timeout | 30 Seconds |
| Maximum Visibility Timeout | 12 Hours |
| Maximum Message Size | 256 KB |
| Maximum Delay | 15 Minutes |
| Maximum Long Polling | 20 Seconds |
| Default Retention | 4 Days |
| Maximum Retention | 14 Days |
| Batch Size | 10 Messages |
| Monitoring Service | Amazon CloudWatch |
| Audit Service | AWS CloudTrail |

---

# Production Deployment Checklist

- ☐ Queue created
- ☐ Visibility Timeout configured
- ☐ Long Polling enabled
- ☐ Dead Letter Queue configured
- ☐ Server-Side Encryption enabled
- ☐ IAM permissions reviewed
- ☐ Queue Policy validated
- ☐ CloudWatch alarms configured
- ☐ CloudTrail enabled
- ☐ Infrastructure as Code committed
- ☐ Consumer is idempotent
- ☐ Monitoring dashboard created

---

# Summary

This cheat sheet consolidates the most important Amazon SQS concepts, limits, commands, configuration settings, and best practices into a single reference document. Keep it handy while developing applications, preparing for interviews, or troubleshooting production systems.