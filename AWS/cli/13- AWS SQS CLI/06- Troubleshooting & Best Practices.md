# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon SQS queues, diagnose message processing failures, monitor queue health, recover from operational issues, and implement production-grade messaging practices using Amazon SQS and the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot Amazon SQS queues
- Diagnose producer and consumer issues
- Resolve message delivery failures
- Debug Dead Letter Queues
- Optimize queue performance
- Recover from production failures
- Apply enterprise messaging best practices

---

# Troubleshooting Workflow

Always troubleshoot from the producer toward the consumer.

```text
Producer

↓

Amazon SQS

↓

Consumer

↓

Application

↓

Database
```

---

# Verify Queue Exists

List queues.

```bash
aws sqs list-queues
```

Retrieve Queue URL.

```bash
aws sqs get-queue-url \
--queue-name orders
```

---

# Verify Queue Attributes

```bash
aws sqs get-queue-attributes \
--queue-url QUEUE_URL \
--attribute-names All
```

Review:

- Visibility Timeout
- Delay Seconds
- Message Retention
- Receive Wait Time
- Redrive Policy
- Encryption

---

# Cannot Send Messages

Possible causes:

- Queue does not exist
- IAM permission denied
- Queue Policy denied
- Incorrect Region
- Invalid Queue URL

---

# QueueDoesNotExist

Verify:

- Queue name
- Queue URL
- AWS Region
- AWS Account

Retrieve the Queue URL again if necessary.

---

# AccessDenied

Verify:

- IAM Role
- IAM Policy
- Queue Policy

Ensure:

```text
Producer

↓

sqs:SendMessage
```

permission exists.

---

# Consumer Cannot Receive Messages

Verify:

- Queue contains messages
- Consumer IAM permissions
- Long Polling configuration
- Visibility Timeout

---

# Messages Stuck in Queue

Possible causes:

- No consumers
- Consumer crashed
- IAM issues
- Worker application stopped

Architecture:

```text
Producer

↓

Amazon SQS

↓

No Consumer
```

Messages remain available until processed.

---

# Messages Processed Multiple Times

Amazon SQS Standard queues provide:

```text
At Least Once
```

delivery.

Applications must tolerate duplicate processing.

Solutions:

- Idempotent consumers
- Deduplication logic
- FIFO queues (when ordering is required)

---

# Visibility Timeout Too Short

Symptoms:

```text
Consumer

↓

Processing

↓

Visibility Timeout

↓

Same Message Received Again
```

Increase Visibility Timeout.

---

# Visibility Timeout Too Long

Symptoms:

```text
Consumer Crash

↓

Message Hidden

↓

Long Delay

↓

Retry
```

Messages remain unavailable longer than necessary.

Choose a timeout slightly longer than expected processing time.

---

# ReceiptHandleIsInvalid

Possible causes:

- Old Receipt Handle
- Message already deleted
- Wrong Queue URL

Always use the latest Receipt Handle returned by `ReceiveMessage`.

---

# InvalidMessageContents

Verify:

- UTF-8 encoding
- Valid JSON
- Maximum message size

Maximum:

```text
256 KB
```

---

# Large Message Problems

For large payloads:

```text
Amazon S3

↓

Store Object

↓

Send Object Key

↓

Amazon SQS
```

Avoid placing large files directly inside messages.

---

# Queue Growing Rapidly

Monitor:

```text
ApproximateNumberOfMessagesVisible
```

Possible causes:

- Slow consumers
- Consumer failures
- Insufficient workers

Scale consumers accordingly.

---

# Oldest Message Increasing

Monitor:

```text
ApproximateAgeOfOldestMessage
```

High values indicate processing delays.

Possible solutions:

- Increase worker count
- Optimize processing
- Reduce external API latency

---

# Empty Receives

Symptoms:

Consumers continuously poll but receive nothing.

Possible causes:

- Empty queue
- Short Polling

Enable Long Polling.

---

# Long Polling Recommendation

Configure:

```text
ReceiveMessageWaitTimeSeconds

↓

20 Seconds
```

Benefits:

- Fewer API calls
- Lower cost
- Better performance

---

# Dead Letter Queue Growing

Possible causes:

- Invalid messages
- Consumer bugs
- Database failures
- External API failures

Never replay messages before identifying the root cause.

---

# Redrive Workflow

```text
Dead Letter Queue

↓

Fix Application

↓

Replay Messages

↓

Main Queue
```

Always validate fixes before replaying production traffic.

---

# FIFO Queue Problems

Verify:

- Queue ends with `.fifo`
- MessageGroupId supplied
- Deduplication ID configured (if required)

---

# Duplicate Messages

Possible causes:

Standard Queue behavior:

```text
At Least Once Delivery
```

Solution:

- Idempotent processing
- Unique business identifiers

---

# CloudWatch Monitoring

Monitor:

- ApproximateNumberOfMessagesVisible
- ApproximateAgeOfOldestMessage
- NumberOfMessagesSent
- NumberOfMessagesReceived
- NumberOfMessagesDeleted
- EmptyReceives

---

# Recommended CloudWatch Alarms

Configure alarms for:

```text
Queue Depth High
```

```text
Oldest Message Age High
```

```text
Dead Letter Queue Size
```

```text
Consumer Failures
```

---

# Consumer Performance

Monitor:

```text
Receive

↓

Process

↓

Delete
```

Identify bottlenecks during processing.

---

# Lambda Consumer Problems

Verify:

- Event Source Mapping
- Lambda permissions
- Queue ARN
- Batch size
- Visibility Timeout

---

# ECS Worker Problems

Verify:

- Running tasks
- IAM Task Role
- Network connectivity
- Queue permissions
- Worker logs

---

# Queue Policy Problems

Review:

- Principal
- Action
- Resource
- Conditions

Verify that both IAM Policies and Queue Policies allow access.

---

# Encryption Issues

If using AWS KMS:

Verify:

- KMS Key
- IAM permissions
- Key policy

Common error:

```text
KMSAccessDeniedException
```

---

# Cross-Account Problems

Verify:

- Queue Policy
- IAM Role
- Account ID
- Region

Cross-account access requires permissions on both sides.

---

# CloudTrail

Review CloudTrail for:

- Queue creation
- Queue deletion
- Permission changes
- Queue attribute updates
- Message API activity

---

# Production Health Checklist

Daily:

- Queue depth
- DLQ size
- Oldest message age
- Consumer health
- Failed messages
- CloudWatch alarms

---

# Weekly Checklist

Review:

- Queue Policies
- IAM Roles
- Encryption settings
- Visibility Timeout
- Long Polling configuration
- Redrive Policy
- Queue naming

---

# Production Best Practices

## Enable Long Polling

Reduces cost and improves responsiveness.

---

## Configure Dead Letter Queues

Every production queue should have a DLQ.

---

## Delete Messages After Success

Never delete before processing completes.

---

## Keep Messages Small

Store large payloads in Amazon S3.

---

## Use Idempotent Consumers

Protect against duplicate deliveries.

---

## Monitor Queue Depth

Scale consumers before backlogs grow.

---

## Secure Every Queue

Enable:

- IAM
- Queue Policies
- Encryption
- CloudTrail

---

## Configure CloudWatch Alarms

Detect issues before they impact users.

---

# Real-World Workflow

```text
Application Error

↓

CloudWatch Alarm

↓

Review Queue Metrics

↓

Inspect DLQ

↓

Fix Consumer

↓

Replay Messages

↓

Production
```

---

# Architecture Note

```text
Producer
      │
      ▼
Amazon SQS
      │
      ├── CloudWatch
      ├── CloudTrail
      ├── Dead Letter Queue
      └── Consumer
              │
              ▼
Database
```

A production Amazon SQS deployment should be continuously monitored using CloudWatch, secured with IAM and Queue Policies, protected by Dead Letter Queues, and designed with idempotent consumers to ensure reliable message processing.

---

# Interview Note

### Question

**How would you troubleshoot a growing Amazon SQS queue in production?**

### Answer

I would first examine CloudWatch metrics such as **ApproximateNumberOfMessagesVisible** and **ApproximateAgeOfOldestMessage** to determine whether consumers are keeping up with incoming traffic. Next, I would verify that the consumer applications (Lambda, ECS, or EC2 workers) are healthy and have the required IAM permissions. I would review application logs, inspect the Dead Letter Queue for failed messages, and confirm that the Visibility Timeout is appropriate. If the workload exceeds current processing capacity, I would scale the consumers horizontally while continuing to monitor queue depth and processing latency until the backlog is cleared.

---

# Key Takeaways

- Troubleshoot Amazon SQS from producers to consumers.
- Queue depth and oldest message age are key operational metrics.
- Long Polling improves efficiency and reduces costs.
- Dead Letter Queues isolate failed messages for analysis.
- Idempotent consumers are essential because Standard queues provide at-least-once delivery.
- CloudWatch and CloudTrail are primary tools for monitoring and auditing.
- Combining monitoring, secure access controls, retries, and scalable consumers results in a resilient production messaging system.