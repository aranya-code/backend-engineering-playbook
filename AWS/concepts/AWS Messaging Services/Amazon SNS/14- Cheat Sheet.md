# Introduction

This chapter is a quick reference guide for Amazon SNS.

Use it for:

- Interview preparation
- AWS Certification revision
- Daily development
- Production troubleshooting
- Architecture discussions

---

# Amazon SNS at a Glance

| Feature | Value |
|----------|-------|
| Service Type | Publish/Subscribe Messaging |
| Communication Model | Push |
| Message Storage | No |
| Topic Types | Standard, FIFO |
| Delivery Model | One-to-Many |
| Maximum Message Size | 256 KB |
| Encryption | AWS KMS |
| Monitoring | Amazon CloudWatch |
| Auditing | AWS CloudTrail |

---

# Core Components

```
Publisher

↓

SNS Topic

↓

Subscription

↓

Subscriber
```

---

# Supported Subscription Protocols

| Protocol | Description |
|----------|-------------|
| Amazon SQS | Queue |
| AWS Lambda | Serverless |
| HTTP | REST Endpoint |
| HTTPS | Secure REST Endpoint |
| Email | Email Notification |
| Email-JSON | JSON Email |
| SMS | Text Message |
| Mobile Push | Android / iOS Notifications |

---

# Message Flow

```
Publisher

↓

Publish()

↓

SNS Topic

↓

Subscribers

↓

Delivered
```

---

# SNS vs SQS

| Amazon SNS | Amazon SQS |
|------------|------------|
| Publish / Subscribe | Message Queue |
| Push Model | Pull Model |
| Broadcast Messages | Store Messages |
| Multiple Subscribers | One Consumer per Message |
| No Storage | Durable Storage |

---

# Standard Topic

### Features

- High throughput
- Best-effort ordering
- At-least-once delivery
- Supports all subscription protocols

### Best For

- Notifications
- Alerts
- Event broadcasting
- Fan-Out architecture

---

# FIFO Topic

### Features

- Strict ordering
- Message deduplication
- Exactly-once delivery (within the deduplication window)
- Supports FIFO SQS queues

### Requirements

```
Topic Name

↓

orders.fifo
```

---

# Message Filtering

```
Publisher

↓

Message Attributes

↓

Filter Policy

↓

Matching Subscriber
```

Benefits

- Lower cost
- Better scalability
- Reduced processing
- Cleaner architecture

---

# Security Features

- IAM Policies
- Topic Policies
- AWS KMS Encryption
- HTTPS
- CloudTrail
- CloudWatch

---

# IAM vs Topic Policy

| IAM Policy | Topic Policy |
|------------|--------------|
| Identity-based | Resource-based |
| Attached to Users/Roles | Attached to Topic |
| Controls User Permissions | Controls Topic Access |

---

# Monitoring Metrics

| Metric | Purpose |
|----------|----------|
| NumberOfMessagesPublished | Published messages |
| NumberOfNotificationsDelivered | Successful deliveries |
| NumberOfNotificationsFailed | Failed deliveries |
| NumberOfNotificationsFilteredOut | Filtered messages |
| PublishSize | Payload size |

---

# Common AWS Integrations

```
Amazon S3

↓

Amazon SNS

↓

Amazon SQS

↓

Lambda

↓

CloudWatch

↓

Email

↓

SMS
```

---

# AWS CLI Commands

## Create Topic

```bash
aws sns create-topic \
    --name order-events
```

---

## List Topics

```bash
aws sns list-topics
```

---

## Publish Message

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Hello World"
```

---

## Subscribe

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol email \
    --notification-endpoint admin@example.com
```

---

## List Subscriptions

```bash
aws sns list-subscriptions
```

---

## Delete Topic

```bash
aws sns delete-topic \
    --topic-arn TOPIC_ARN
```

---

# Boto3 Quick Reference

## Create Client

```python
import boto3

sns = boto3.client("sns")
```

---

## Create Topic

```python
sns.create_topic(
    Name="order-events"
)
```

---

## Publish

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Hello AWS"
)
```

---

## Subscribe

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="email",
    Endpoint="admin@example.com"
)
```

---

## Delete Topic

```python
sns.delete_topic(
    TopicArn=TOPIC_ARN
)
```

---

# Common Topic Attributes

| Attribute | Purpose |
|------------|----------|
| DisplayName | Display name for SMS |
| Policy | Topic Policy |
| KmsMasterKeyId | Encryption Key |
| FifoTopic | FIFO Support |
| ContentBasedDeduplication | Automatic Deduplication |

---

# Common Limits

| Resource | Limit |
|----------|-------|
| Maximum Message Size | 256 KB |
| Topic Types | Standard / FIFO |
| Message Delivery | Push |
| Encryption | AWS KMS |
| Retry | Protocol Dependent |

---

# Common Use Cases

- Order Processing
- Payment Notifications
- User Registration
- CloudWatch Alerts
- Event Broadcasting
- Serverless Applications
- Fan-Out Architecture
- Mobile Notifications
- CI/CD Notifications
- Monitoring Systems

---

# Architecture Patterns

```
Publisher

↓

SNS

↓

SQS

↓

Workers
```

---

```
Publisher

↓

SNS

↓

Lambda
```

---

```
CloudWatch Alarm

↓

SNS

↓

Email

↓

SMS
```

---

```
Amazon S3

↓

SNS

↓

Lambda

↓

Image Processing
```

---

# Best Practices Checklist

| Practice | Recommended |
|----------|-------------|
| Use Business-Specific Topics | ✅ |
| Enable Server-Side Encryption | ✅ |
| Use HTTPS Endpoints | ✅ |
| Configure CloudWatch Alarms | ✅ |
| Use IAM Roles | ✅ |
| Apply Least Privilege | ✅ |
| Use Message Filtering | ✅ |
| Use SNS + SQS | ✅ |
| Enable CloudTrail | ✅ |
| Document Event Schemas | ✅ |

---

# Common Mistakes

❌ Using SNS as a Queue

❌ Sending Large Payloads

❌ Ignoring Message Filtering

❌ Mixing Multiple Business Domains

❌ Forgetting Subscription Confirmation

❌ Using HTTP Instead of HTTPS

❌ Granting `sns:*` Permissions

❌ Ignoring CloudWatch Metrics

---

# Interview Quick Facts

| Question | Answer |
|----------|--------|
| Communication Model | Publish / Subscribe |
| Delivery Model | Push |
| Stores Messages | No |
| Topic Types | Standard, FIFO |
| FIFO Topic Suffix | `.fifo` |
| Supports Message Filtering | Yes |
| Encryption | AWS KMS |
| Monitoring | CloudWatch |
| Auditing | CloudTrail |
| Common Integration | Amazon SQS |

---

# Production Checklist

- ☐ Topics created
- ☐ Naming conventions followed
- ☐ IAM permissions reviewed
- ☐ Topic Policies configured
- ☐ Server-Side Encryption enabled
- ☐ HTTPS endpoints configured
- ☐ Message Filtering enabled
- ☐ CloudWatch monitoring enabled
- ☐ CloudWatch alarms configured
- ☐ CloudTrail enabled
- ☐ Event schemas documented
- ☐ Subscriber health verified

---

# Summary

This cheat sheet provides a concise reference for Amazon SNS concepts, architecture, security, monitoring, AWS CLI commands, Boto3 examples, and production best practices. Keep it as a quick revision guide for interviews, AWS certification preparation, and day-to-day development of event-driven applications.