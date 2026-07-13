# Fan-Out Pattern, Filtering & Delivery Policies

> Learn how Amazon SNS distributes messages to multiple subscribers using the Fan-Out pattern, controls message delivery with Filter Policies, manages retries using Delivery Policies, supports FIFO Topics, and builds scalable event-driven architectures.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand the Fan-Out messaging pattern
- Configure multiple subscribers
- Configure Message Filtering
- Configure Filter Policies
- Configure Delivery Policies
- Understand Retry Policies
- Configure FIFO Topics
- Build scalable event-driven architectures

---

# Fan-Out Pattern

The Fan-Out pattern allows a single published message to be delivered to multiple independent subscribers.

Architecture:

```text
Publisher

↓

Amazon SNS

│

├── Subscriber A

├── Subscriber B

├── Subscriber C

└── Subscriber D
```

Each subscriber receives its own copy of the message.

---

# Why Fan-Out?

Without SNS:

```text
Application

├── Email Service

├── Inventory Service

├── Billing Service

└── Analytics Service
```

The application must notify every service individually.

With SNS:

```text
Application

↓

Amazon SNS

↓

All Subscribers
```

The publisher only sends one message.

---

# Real-World Example

An order is created.

```text
Order Created

↓

Amazon SNS

│

├── Billing Queue

├── Inventory Queue

├── Email Service

├── Analytics

└── Fraud Detection
```

Every service processes the same business event independently.

---

# Fan-Out with Amazon SQS

The most common production architecture:

```text
Backend API

↓

Amazon SNS

│

├── Orders Queue

├── Billing Queue

├── Shipping Queue

└── Analytics Queue
```

Each SQS queue has its own consumers.

---

# Benefits of Fan-Out

- Loose coupling
- Independent scaling
- Fault isolation
- Easier maintenance
- Event-driven architecture

---

# Message Filtering

Not every subscriber needs every message.

Amazon SNS supports:

```text
Message Filtering
```

Subscribers receive only relevant events.

---

# Example

Published events:

```text
Order Created

Order Cancelled

Payment Failed

Inventory Updated
```

Inventory service only wants:

```text
Inventory Updated
```

Message filtering prevents unnecessary processing.

---

# Filter Policy

A Filter Policy defines which messages are delivered.

Architecture:

```text
Publisher

↓

Amazon SNS

↓

Filter Policy

↓

Subscriber
```

---

# Message Attributes

Filtering uses message attributes.

Example:

```json
{
    "eventType": "OrderCreated",
    "priority": "high"
}
```

---

# Publish with Attributes

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message "Order Created" \
--message-attributes '{
  "eventType":{
    "DataType":"String",
    "StringValue":"OrderCreated"
  }
}'
```

---

# Example Filter Policy

```json
{
  "eventType": [
    "OrderCreated",
    "PaymentCompleted"
  ]
}
```

Only matching events reach the subscriber.

---

# Priority Filtering

Messages:

```text
High

Medium

Low
```

Subscriber:

```text
High Only
```

SNS automatically filters the rest.

---

# Regional Filtering

Example:

```json
{
  "region": [
    "us-east-1",
    "eu-west-1"
  ]
}
```

Subscribers receive only selected Regions.

---

# Filter Policy Workflow

```text
Publisher

↓

SNS Topic

↓

Filter Policy

↓

Matching Subscriber
```

Non-matching subscribers receive nothing.

---

# Delivery Policies

SNS controls delivery retries.

```text
Publisher

↓

Amazon SNS

↓

Retry

↓

Subscriber
```

---

# Retry Workflow

If delivery fails:

```text
Publish

↓

Failure

↓

Retry

↓

Success
```

---

# Delivery Policy Components

Typical configuration includes:

- Retry count
- Retry delay
- Backoff strategy
- Maximum retry duration

---

# Delivery Status

Possible outcomes:

```text
Delivered
```

```text
Failed
```

```text
Retrying
```

---

# FIFO Topics

FIFO Topics provide:

- Ordered publishing
- Exactly-once delivery

Topic name:

```text
payments.fifo
```

---

# FIFO Fan-Out

```text
Publisher

↓

FIFO Topic

↓

FIFO Queue A

↓

FIFO Queue B
```

Ordering is preserved throughout the workflow.

---

# Message Groups

FIFO Topics use:

```text
MessageGroupId
```

Example:

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message "Payment Completed" \
--message-group-id payments
```

---

# Deduplication

FIFO Topics support:

```text
Exactly Once Publishing
```

Duplicate messages within the deduplication window are ignored.

---

# Content-Based Deduplication

Enable automatic deduplication.

```text
Content

↓

Hash

↓

Duplicate Detection
```

---

# Fan-Out vs Queue

| SNS Fan-Out | SQS Queue |
|--------------|-----------|
| Multiple subscribers | One consumer group |
| Push delivery | Pull delivery |
| Broadcast events | Reliable buffering |
| Pub/Sub | Queue |

---

# Enterprise Architecture

```text
Customer

↓

Backend API

↓

Amazon SNS

│

├── Billing Queue

├── Shipping Queue

├── Inventory Queue

├── Analytics Queue

└── Notification Queue
```

Each team owns its own consumer.

---

# Microservices Architecture

```text
Order Service

↓

Amazon SNS

│

├── Inventory Service

├── Billing Service

├── Email Service

├── Reporting Service

└── Search Service
```

No service directly depends on another.

---

# CloudWatch Metrics

Monitor:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- PublishSize

---

# Common Errors

## Subscriber Receives Nothing

Verify:

- Filter Policy
- Message Attributes
- Subscription
- Topic ARN

---

## Message Not Delivered

Verify:

- Endpoint health
- Delivery Policy
- IAM permissions
- Queue Policy (SQS)

---

## Duplicate Events

Possible causes:

- Standard Topic
- Consumer retry
- Non-idempotent consumer

---

## FIFO Ordering Problems

Verify:

- FIFO Topic
- FIFO Queue
- MessageGroupId
- Deduplication settings

---

# Production Best Practices

- Use SNS Fan-Out to decouple services.
- Filter messages instead of creating many Topics.
- Use Message Attributes consistently.
- Configure retry policies for HTTP endpoints.
- Monitor failed deliveries.
- Use FIFO Topics only when ordering is required.
- Keep Topics business-event oriented.
- Make consumers idempotent.
- Combine SNS with SQS for reliable processing.

---

# Real-World Workflow

```text
Customer Order

↓

Amazon SNS

↓

Billing Queue

↓

Shipping Queue

↓

Inventory Queue

↓

Notification Queue

↓

Analytics Queue
```

---

# Architecture Note

```text
Publisher
      │
      ▼
Amazon SNS Topic
      │
      ├── Filter Policy
      │      │
      │      ▼
      ├── Amazon SQS
      ├── AWS Lambda
      ├── HTTPS Endpoint
      ├── Email
      └── SMS
```

A production Amazon SNS deployment distributes business events through a Fan-Out architecture while using Filter Policies to ensure each subscriber receives only the events it needs, reducing unnecessary processing and improving scalability.

---

# Interview Note

### Question

**What problem does the Amazon SNS Fan-Out pattern solve?**

### Answer

The Fan-Out pattern allows a single published event to be delivered simultaneously to multiple independent subscribers without the publisher knowing about them. This decouples services, improves scalability, enables independent deployments, and simplifies event-driven architectures. A common implementation is Amazon SNS publishing to multiple Amazon SQS queues, where each microservice processes events independently.

---

# Key Takeaways

- Fan-Out enables one publisher to notify many subscribers.
- Filter Policies reduce unnecessary message delivery.
- Message Attributes determine filtering behavior.
- Delivery Policies manage retries for failed deliveries.
- FIFO Topics provide ordered and exactly-once publishing.
- SNS and SQS together form one of AWS's most common event-driven architecture patterns.
- Production systems use Fan-Out to build loosely coupled, independently scalable microservices.