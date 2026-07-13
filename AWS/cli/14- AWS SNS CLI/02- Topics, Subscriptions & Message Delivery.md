# Topics, Subscriptions & Message Delivery

> Learn how to create and manage Amazon SNS Topics, configure subscriptions, publish messages, and deliver notifications to multiple endpoint types using the AWS CLI. This chapter covers Topic management, subscription lifecycle, supported protocols, message publishing, FIFO Topics, and production delivery workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create SNS Topics
- Manage subscriptions
- Publish notifications
- Understand message delivery
- Configure Email, SMS, SQS, Lambda, and HTTP subscriptions
- Work with FIFO Topics
- Build reliable notification systems

---

# SNS Topic

A Topic is the central communication channel in Amazon SNS.

```text
Publisher

↓

SNS Topic

↓

Subscribers
```

Publishers never communicate directly with subscribers.

---

# Topic ARN

Every Topic has a unique ARN.

Example:

```text
arn:aws:sns:ap-south-1:123456789012:order-events
```

Most AWS CLI operations require the Topic ARN.

---

# Create Topic

```bash
aws sns create-topic \
--name order-events
```

Response:

```json
{
    "TopicArn": "arn:aws:sns:ap-south-1:123456789012:order-events"
}
```

---

# List Topics

```bash
aws sns list-topics
```

---

# View Topic Details

```bash
aws sns get-topic-attributes \
--topic-arn TOPIC_ARN
```

Displays:

- Topic ARN
- Owner
- Display Name
- Policy
- Encryption
- FIFO status

---

# Delete Topic

```bash
aws sns delete-topic \
--topic-arn TOPIC_ARN
```

Deleting a Topic also deletes all associated subscriptions.

---

# Topic Naming Strategy

Recommended examples:

```text
order-events

payment-events

notification-events

user-events
```

FIFO examples:

```text
payment-events.fifo

inventory-events.fifo
```

---

# Subscription

A Subscription connects a Topic to an endpoint.

```text
SNS Topic

↓

Subscription

↓

Endpoint
```

One Topic can have multiple subscriptions.

---

# Supported Protocols

Amazon SNS supports:

```text
Amazon SNS

│

├── Amazon SQS

├── AWS Lambda

├── Email

├── SMS

├── HTTP

└── HTTPS
```

---

# Subscription Workflow

```text
Publisher

↓

SNS Topic

↓

Subscription

↓

Endpoint
```

---

# Email Subscription

Create an email subscription.

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol email \
--notification-endpoint user@example.com
```

---

# Email Confirmation

Email subscriptions require confirmation.

Workflow:

```text
Email

↓

Confirmation Link

↓

Confirmed Subscription
```

Until confirmed:

```text
PendingConfirmation
```

---

# List Subscriptions

```bash
aws sns list-subscriptions
```

---

# List Topic Subscriptions

```bash
aws sns list-subscriptions-by-topic \
--topic-arn TOPIC_ARN
```

---

# SMS Subscription

Publish directly to a phone number.

```bash
aws sns publish \
--phone-number +15551234567 \
--message "Verification Code: 123456"
```

Useful for:

- OTPs
- Alerts
- Emergency notifications

---

# HTTP Subscription

Subscribe an HTTP endpoint.

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol http \
--notification-endpoint http://example.com/webhook
```

---

# HTTPS Subscription

Production recommendation:

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol https \
--notification-endpoint https://api.example.com/webhook
```

HTTPS protects message delivery in transit.

---

# Lambda Subscription

Connect a Lambda function.

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol lambda \
--notification-endpoint LAMBDA_ARN
```

Workflow:

```text
SNS

↓

Lambda

↓

Processing
```

---

# Amazon SQS Subscription

One of the most common integrations.

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol sqs \
--notification-endpoint QUEUE_ARN
```

Architecture:

```text
SNS

↓

SQS

↓

Workers
```

---

# Publish Message

Publish a notification.

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message "Order Created"
```

Every subscriber receives the message.

---

# Publish JSON Message

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message '{"orderId":1001,"status":"created"}'
```

---

# Subject Line

Email notifications support a subject.

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--subject "Order Update" \
--message "Your order has shipped."
```

---

# Message Attributes

Messages can include metadata.

Example:

```text
Message

│

├── Body

├── Subject

└── Attributes
```

Useful attributes:

- Event Type
- Customer ID
- Region
- Priority

---

# FIFO Topics

FIFO Topics guarantee:

- Ordered delivery
- Exactly-once publishing

Topic name must end with:

```text
.fifo
```

---

# Create FIFO Topic

```bash
aws sns create-topic \
--name payment-events.fifo \
--attributes FifoTopic=true
```

---

# Publish to FIFO Topic

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message "Payment Received" \
--message-group-id payments
```

---

# Message Delivery Workflow

```text
Publisher

↓

SNS Topic

↓

Subscribers

↓

Processing
```

Every subscriber receives an independent copy.

---

# Delivery Status

SNS tracks delivery success.

Possible outcomes:

```text
Delivered
```

```text
Failed
```

```text
Pending
```

Delivery behavior depends on the subscriber type.

---

# Message Size

Maximum SNS message size:

```text
256 KB
```

For larger payloads:

```text
Amazon S3

↓

Store Object

↓

Publish Object Key
```

---

# Delivery Architecture

```text
Backend API

↓

Amazon SNS

│

├── Email

├── Lambda

├── SQS

└── HTTPS API
```

---

# Common Errors

## TopicNotFound

Verify:

- Topic ARN
- Region
- AWS Account

---

## InvalidParameter

Verify:

- Protocol
- Endpoint
- ARN

---

## SubscriptionPendingConfirmation

The recipient must confirm the subscription.

---

## EndpointDisabled

Verify:

- Email
- SMS
- Lambda
- HTTP endpoint availability

---

# Production Best Practices

- Use meaningful Topic names.
- Prefer HTTPS over HTTP.
- Confirm Email subscriptions.
- Use SQS subscriptions for reliable processing.
- Keep notification payloads small.
- Store large payloads in Amazon S3.
- Use FIFO Topics only when ordering is required.
- Monitor delivery failures.
- Remove unused subscriptions.

---

# Real-World Workflow

```text
Order Created

↓

Amazon SNS

│

├── Customer Email

├── Billing Queue

├── Inventory Queue

└── Analytics Lambda
```

---

# Architecture Note

```text
Publisher
      │
      ▼
Amazon SNS Topic
      │
      ├── Email
      ├── Amazon SQS
      ├── AWS Lambda
      ├── HTTPS Endpoint
      └── SMS
```

A production Amazon SNS Topic distributes a single published message to multiple independent subscribers, enabling loosely coupled and highly scalable event-driven architectures.

---

# Interview Note

### Question

**What is the difference between an Amazon SNS Topic and an Amazon SQS Queue?**

### Answer

An Amazon SNS Topic implements the publish-subscribe messaging model, where a single published message is pushed to multiple subscribers such as Amazon SQS queues, Lambda functions, Email, SMS, or HTTP endpoints. An Amazon SQS Queue implements a message queue model, where messages are stored until consumers retrieve and process them. SNS is optimized for broadcasting events, while SQS is optimized for reliable asynchronous processing.

---

# Key Takeaways

- Topics are the central communication channel in Amazon SNS.
- Subscriptions connect Topics to endpoints.
- Amazon SNS supports Email, SMS, Lambda, SQS, HTTP, and HTTPS endpoints.
- Every published message is delivered independently to each subscriber.
- FIFO Topics provide ordered message delivery.
- HTTPS should be preferred over HTTP in production.
- Amazon SNS and Amazon SQS are commonly used together to build scalable event-driven architectures.