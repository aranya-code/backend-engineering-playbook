# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon SQS CLI commands, queue management workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used Amazon SQS CLI commands
- Manage queues efficiently
- Send and receive messages
- Configure security
- Configure Dead Letter Queues
- Monitor queue health
- Troubleshoot production messaging systems
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon SQS consists of numerous operational concepts:

- Queues
- Messages
- Producers
- Consumers
- Visibility Timeout
- Long Polling
- Dead Letter Queues
- Queue Policies
- Encryption
- Monitoring

Experienced engineers focus on:

- Reliability
- Scalability
- Fault tolerance
- Security
- Automation
- Monitoring

This chapter provides a practical operational reference.

---

# CLI Namespace

General syntax:

```bash
aws sqs <operation>
```

Examples:

```bash
aws sqs create-queue
```

```bash
aws sqs send-message
```

```bash
aws sqs receive-message
```

---

# Queue Commands

## List Queues

```bash
aws sqs list-queues
```

---

## Create Queue

```bash
aws sqs create-queue
```

---

## Create FIFO Queue

```bash
aws sqs create-queue \
--queue-name orders.fifo \
--attributes FifoQueue=true
```

---

## Delete Queue

```bash
aws sqs delete-queue
```

---

## Get Queue URL

```bash
aws sqs get-queue-url
```

---

## Get Queue Attributes

```bash
aws sqs get-queue-attributes
```

---

## Modify Queue Attributes

```bash
aws sqs set-queue-attributes
```

---

# Message Commands

## Send Message

```bash
aws sqs send-message
```

---

## Receive Message

```bash
aws sqs receive-message
```

---

## Delete Message

```bash
aws sqs delete-message
```

---

## Send Batch

```bash
aws sqs send-message-batch
```

---

## Delete Batch

```bash
aws sqs delete-message-batch
```

---

## Change Visibility Timeout

```bash
aws sqs change-message-visibility
```

---

# Common Queue Attributes

| Attribute | Purpose |
|-----------|----------|
| VisibilityTimeout | Prevent duplicate processing |
| DelaySeconds | Delay message delivery |
| MessageRetentionPeriod | Message lifetime |
| ReceiveMessageWaitTimeSeconds | Long Polling |
| RedrivePolicy | Dead Letter Queue |
| KmsMasterKeyId | KMS Encryption |
| SqsManagedSseEnabled | SSE-SQS |

---

# Standard vs FIFO

| Feature | Standard | FIFO |
|----------|----------|------|
| Ordering | Best Effort | Guaranteed |
| Delivery | At Least Once | Exactly Once |
| Throughput | Very High | Lower |
| Deduplication | No | Yes |
| Message Groups | No | Yes |

---

# Visibility Timeout

Workflow:

```text
Receive

↓

Invisible

↓

Process

↓

Delete
```

Recommendation:

```text
Visibility Timeout

>

Maximum Processing Time
```

---

# Long Polling

Recommended:

```text
20 Seconds
```

Benefits:

- Lower API cost
- Fewer empty responses
- Faster processing

---

# Dead Letter Queue

Workflow:

```text
Main Queue

↓

Retry

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

---

# Redrive Policy

Defines:

```text
Maximum Receive Count

↓

Move To DLQ
```

---

# Queue Architecture

```text
Producer

↓

Amazon SQS

↓

Consumer

↓

Database
```

---

# Event-Driven Architecture

```text
Application

↓

Amazon SQS

↓

Lambda

↓

Amazon RDS
```

---

# Fan-Out Architecture

```text
Application

↓

Amazon SNS

│

├── Queue A

├── Queue B

└── Queue C
```

---

# Worker Scaling

```text
Queue Depth

↓

CloudWatch

↓

Auto Scaling

↓

Workers
```

---

# CloudWatch Metrics

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

- Queue Depth
- Oldest Message Age
- Dead Letter Queue Size
- Consumer Failures
- Empty Receives

---

# Security Checklist

Every production queue should have:

- □ IAM Policies
- □ Queue Policies
- □ Server-Side Encryption
- □ AWS KMS (if required)
- □ CloudTrail enabled
- □ CloudWatch monitoring
- □ Least privilege access

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| QueueDoesNotExist | Invalid Queue URL | Verify queue |
| AccessDenied | IAM or Queue Policy | Review permissions |
| ReceiptHandleIsInvalid | Old Receipt Handle | Use latest handle |
| InvalidMessageContents | Invalid payload | Validate UTF-8/JSON |
| KMSAccessDeniedException | KMS permission issue | Review KMS policy |
| OverLimit | Too many inflight messages | Delete processed messages |
| AWS.SimpleQueueService.NonExistentQueue | Queue deleted | Verify Queue URL |

---

# Production Deployment Checklist

Before deploying:

- □ Long Polling enabled
- □ Visibility Timeout configured
- □ Dead Letter Queue configured
- □ Redrive Policy configured
- □ Encryption enabled
- □ CloudWatch alarms configured
- □ Consumers are idempotent
- □ Batch processing enabled
- □ Monitoring dashboards created

---

# Daily Operations Checklist

Review:

- Queue depth
- DLQ size
- Consumer health
- Message age
- Failed processing
- CloudWatch alarms
- Queue permissions

---

# Weekly Operations Checklist

Review:

- Queue Policies
- IAM Roles
- Encryption
- Long Polling configuration
- Visibility Timeout
- Redrive Policy
- Consumer performance
- CloudWatch dashboards

---

# Architecture Comparison

## Synchronous

```text
API

↓

Service

↓

Database
```

---

## Asynchronous

```text
API

↓

Amazon SQS

↓

Worker

↓

Database
```

---

# Amazon SQS Integrations

| Service | Purpose |
|----------|----------|
| Lambda | Event processing |
| ECS | Long-running workers |
| EC2 | Worker applications |
| SNS | Fan-out messaging |
| EventBridge | Event routing |
| Step Functions | Workflow integration |
| AWS Batch | Large compute jobs |

---

# Production Architecture

```text
Users
      │
      ▼
Application Load Balancer
      │
      ▼
Backend API
      │
      ▼
Amazon SQS
      │
      ├── AWS Lambda
      ├── Amazon ECS
      ├── Dead Letter Queue
      ├── CloudWatch
      └── CloudTrail
              │
              ▼
Amazon RDS
```

---

# Interview Questions

## 1. What is Amazon SQS?

**Answer**

Amazon SQS is AWS's fully managed message queue service that enables asynchronous communication between distributed applications. It improves scalability, reliability, and fault tolerance by decoupling producers and consumers.

---

## 2. What is the difference between Standard and FIFO queues?

**Answer**

Standard queues provide very high throughput with at-least-once delivery and best-effort ordering. FIFO queues guarantee message ordering, exactly-once processing, and require a Message Group ID, making them suitable for financial systems, payments, and inventory management.

---

## 3. What is Visibility Timeout?

**Answer**

Visibility Timeout is the period during which a received message is temporarily hidden from other consumers. It prevents multiple consumers from processing the same message simultaneously. If the consumer fails to delete the message before the timeout expires, the message becomes visible again.

---

## 4. What is a Dead Letter Queue (DLQ)?

**Answer**

A Dead Letter Queue stores messages that fail processing after a configured number of retries. It prevents infinite retry loops, isolates problematic messages, and allows operators to investigate and replay failed messages after fixing the underlying issue.

---

## 5. Why should consumers be idempotent?

**Answer**

Standard queues provide at-least-once delivery, meaning duplicate messages can occur. Consumers should therefore be idempotent so that processing the same message multiple times does not produce incorrect results or duplicate business operations.

---

## 6. What is Long Polling?

**Answer**

Long Polling allows consumers to wait for messages before returning a response, reducing empty responses, lowering API costs, and improving message retrieval efficiency. AWS recommends enabling Long Polling for production queues.

---

## 7. What is a Message Group in FIFO queues?

**Answer**

A Message Group is a logical grouping of related messages that guarantees strict ordering within that group. Multiple Message Groups allow FIFO queues to process different groups in parallel while preserving ordering within each group.

---

## 8. How does Amazon SQS integrate with AWS Lambda?

**Answer**

Amazon SQS integrates with Lambda through an Event Source Mapping. AWS continuously polls the queue, invokes the Lambda function with batches of messages, and automatically deletes successfully processed messages. Failed messages are retried according to the Visibility Timeout and Redrive Policy.

---

## 9. How would you troubleshoot a growing Amazon SQS queue?

**Answer**

I would review CloudWatch metrics such as queue depth and oldest message age, verify that consumers are healthy, inspect Dead Letter Queues for failed messages, confirm that Visibility Timeout is configured correctly, and scale consumers horizontally if the workload exceeds processing capacity.

---

## 10. How do you secure an Amazon SQS queue?

**Answer**

Production queues should use IAM Roles, Queue Policies, Server-Side Encryption, AWS KMS where appropriate, CloudTrail auditing, CloudWatch monitoring, and VPC Endpoints for private access. Access should follow the principle of least privilege.

---

# Senior Engineer Tips

Experienced backend and cloud engineers typically:

- Use Standard queues unless ordering is required.
- Configure a Dead Letter Queue for every production queue.
- Enable Long Polling on all production queues.
- Make every consumer idempotent.
- Keep message payloads small and store large objects in Amazon S3.
- Monitor queue depth continuously using CloudWatch.
- Scale consumers automatically based on queue metrics.
- Encrypt every production queue.
- Use SNS with SQS to implement fan-out architectures.
- Review and test Redrive Policies regularly.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Queues | `aws sqs list-queues` |
| Create Queue | `aws sqs create-queue` |
| Get Queue URL | `aws sqs get-queue-url` |
| View Queue Attributes | `aws sqs get-queue-attributes` |
| Send Message | `aws sqs send-message` |
| Receive Message | `aws sqs receive-message` |
| Delete Message | `aws sqs delete-message` |
| Send Batch | `aws sqs send-message-batch` |
| Delete Batch | `aws sqs delete-message-batch` |
| Delete Queue | `aws sqs delete-queue` |

---

# Final Thoughts

Amazon SQS is one of the foundational building blocks of modern cloud-native architectures. It enables loosely coupled services, asynchronous processing, automatic retries, fault isolation, and horizontal scalability. When combined with Dead Letter Queues, CloudWatch, IAM, AWS KMS, Amazon SNS, AWS Lambda, and Amazon ECS, Amazon SQS provides a highly reliable messaging platform capable of supporting enterprise-scale distributed systems.

---
