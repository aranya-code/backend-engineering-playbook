# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon SNS CLI commands, Topic management workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used Amazon SNS CLI commands
- Manage Topics and Subscriptions
- Publish notifications
- Configure security
- Integrate SNS with AWS services
- Monitor Topic health
- Troubleshoot production notification systems
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon SNS consists of several operational components:

- Topics
- Publishers
- Subscribers
- Subscriptions
- Message Filtering
- Delivery Policies
- Security
- Encryption
- Monitoring

Experienced engineers focus on:

- Scalability
- Reliability
- Event-driven design
- Security
- Automation
- Monitoring

This chapter provides a practical operational reference.

---

# CLI Namespace

General syntax:

```bash
aws sns <operation>
```

Examples:

```bash
aws sns create-topic
```

```bash
aws sns publish
```

```bash
aws sns subscribe
```

---

# Topic Commands

## List Topics

```bash
aws sns list-topics
```

---

## Create Topic

```bash
aws sns create-topic
```

---

## Create FIFO Topic

```bash
aws sns create-topic \
--name payments.fifo \
--attributes FifoTopic=true
```

---

## View Topic Attributes

```bash
aws sns get-topic-attributes
```

---

## Modify Topic Attributes

```bash
aws sns set-topic-attributes
```

---

## Delete Topic

```bash
aws sns delete-topic
```

---

# Subscription Commands

## Subscribe Endpoint

```bash
aws sns subscribe
```

---

## List Subscriptions

```bash
aws sns list-subscriptions
```

---

## List Topic Subscriptions

```bash
aws sns list-subscriptions-by-topic
```

---

## Unsubscribe

```bash
aws sns unsubscribe
```

---

# Publish Commands

## Publish Message

```bash
aws sns publish
```

---

## Publish with Subject

```bash
aws sns publish \
--subject "Order Update"
```

---

## Publish with Attributes

```bash
aws sns publish \
--message-attributes
```

---

## Publish SMS

```bash
aws sns publish \
--phone-number
```

---

# Common Topic Attributes

| Attribute | Purpose |
|-----------|----------|
| DisplayName | Friendly Topic name |
| Policy | Topic access policy |
| KmsMasterKeyId | AWS KMS encryption |
| FifoTopic | FIFO Topic |
| ContentBasedDeduplication | Automatic deduplication |

---

# Supported Subscription Protocols

| Protocol | Typical Use |
|----------|-------------|
| Amazon SQS | Reliable message processing |
| AWS Lambda | Serverless event processing |
| Email | User notifications |
| SMS | OTPs and alerts |
| HTTP | Webhooks |
| HTTPS | Secure webhooks |

---

# Standard vs FIFO Topics

| Feature | Standard | FIFO |
|----------|----------|------|
| Ordering | Best Effort | Guaranteed |
| Delivery | At Least Once | Exactly Once |
| Throughput | Very High | Lower |
| Deduplication | No | Yes |
| Message Groups | No | Yes |

---

# Fan-Out Architecture

```text
Application

↓

Amazon SNS

│

├── Amazon SQS

├── AWS Lambda

├── Email

├── HTTPS

└── SMS
```

---

# SNS + SQS Pattern

```text
Application

↓

Amazon SNS

↓

Multiple Queues

↓

Independent Workers
```

---

# Message Filtering

Workflow:

```text
Publish

↓

Message Attributes

↓

Filter Policy

↓

Subscriber
```

Only matching subscribers receive the message.

---

# Delivery Workflow

```text
Publisher

↓

Amazon SNS

↓

Subscribers

↓

Business Processing
```

---

# CloudWatch Metrics

Monitor:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- PublishSize
- SMSMonthToDateSpentUSD

---

# Recommended CloudWatch Alarms

Configure alarms for:

- Notification Failures
- Publish Errors
- SMS Spending
- Failed Deliveries
- Endpoint Failures

---

# Security Checklist

Every production Topic should have:

- □ IAM Policies
- □ Topic Policies
- □ AWS KMS Encryption
- □ CloudTrail enabled
- □ CloudWatch monitoring
- □ Least Privilege access
- □ Filter Policies reviewed

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| NotFound | Invalid Topic ARN | Verify Topic ARN |
| AuthorizationError | IAM or Topic Policy | Review permissions |
| KMSAccessDeniedException | KMS permission issue | Review KMS policy |
| InvalidParameter | Invalid endpoint or protocol | Verify parameters |
| PendingConfirmation | Email not confirmed | Confirm subscription |
| EndpointDisabled | Subscriber unavailable | Verify endpoint |

---

# Production Deployment Checklist

Before deploying:

- □ Topic created
- □ Topic Policy configured
- □ IAM permissions verified
- □ Encryption enabled
- □ Subscriptions confirmed
- □ Filter Policies configured
- □ CloudWatch alarms created
- □ CloudTrail enabled
- □ Delivery Policies reviewed
- □ Monitoring dashboards created

---

# Daily Operations Checklist

Review:

- Published messages
- Failed deliveries
- Subscription health
- CloudWatch alarms
- CloudTrail events
- SMS spending

---

# Weekly Operations Checklist

Review:

- Topic Policies
- IAM Roles
- AWS KMS configuration
- Filter Policies
- Delivery Policies
- Subscription list
- CloudWatch dashboards

---

# Amazon SNS Integrations

| Service | Purpose |
|----------|----------|
| Amazon SQS | Fan-out messaging |
| AWS Lambda | Serverless processing |
| Amazon EventBridge | Event routing |
| Amazon CloudWatch | Alarm notifications |
| AWS Step Functions | Workflow notifications |
| Amazon ECS | Container event publishing |
| Amazon EC2 | Application notifications |

---

# Event-Driven Architecture

```text
Order Service

↓

Amazon SNS

│

├── Billing

├── Inventory

├── Shipping

├── Analytics

└── Notification
```

---

# Monitoring Architecture

```text
CloudWatch

↓

Amazon SNS

↓

Operations Team
```

---

# Enterprise Architecture

```text
Users
      │
      ▼
Backend API
      │
      ▼
Amazon SNS
      │
      ├── Amazon SQS
      ├── AWS Lambda
      ├── HTTPS Endpoint
      ├── Email
      ├── SMS
      └── CloudWatch
              │
              ▼
Business Services
```

---

# Interview Questions

## 1. What is Amazon SNS?

**Answer**

Amazon SNS is AWS's fully managed publish-subscribe messaging service that enables one publisher to send notifications simultaneously to multiple subscribers. It supports event-driven architectures, fan-out messaging, and integrations with services such as Amazon SQS, AWS Lambda, Email, SMS, HTTP, and HTTPS.

---

## 2. What is the difference between Amazon SNS and Amazon SQS?

**Answer**

Amazon SNS uses a push-based publish-subscribe model that broadcasts messages to multiple subscribers. Amazon SQS uses a pull-based queue model where consumers retrieve messages from a queue. SNS is optimized for event broadcasting, while SQS provides durable message buffering and asynchronous processing.

---

## 3. What is a Topic?

**Answer**

A Topic is the central communication channel in Amazon SNS. Publishers send messages to a Topic, and Amazon SNS distributes those messages to all subscribed endpoints according to their subscription and filter policies.

---

## 4. What is the Fan-Out pattern?

**Answer**

The Fan-Out pattern allows one published message to be delivered simultaneously to multiple independent subscribers. A common implementation uses Amazon SNS to distribute events to multiple Amazon SQS queues so that different microservices can process the same event independently.

---

## 5. What are Filter Policies?

**Answer**

Filter Policies allow subscribers to receive only messages whose attributes match specified criteria. This reduces unnecessary message delivery and enables multiple services to subscribe to the same Topic while processing only relevant events.

---

## 6. What is the purpose of Topic Policies?

**Answer**

Topic Policies are resource-based policies that define which AWS principals or services can publish to or subscribe to an SNS Topic. They are commonly used for cross-account access and AWS service integrations.

---

## 7. How do you secure an Amazon SNS Topic?

**Answer**

Production Topics should use IAM Roles, Topic Policies, AWS KMS encryption, CloudTrail auditing, CloudWatch monitoring, and least-privilege permissions. HTTPS endpoints should be preferred over HTTP for secure message delivery.

---

## 8. Why are Amazon SNS and Amazon SQS commonly used together?

**Answer**

Amazon SNS broadcasts events to multiple Amazon SQS queues, and each queue stores its copy of the message until its consumers process it. This enables reliable delivery, independent scaling, fault isolation, and loose coupling between microservices.

---

## 9. How would you troubleshoot notifications that are not being delivered?

**Answer**

I would verify that the Topic exists, ensure publishing succeeds, confirm that subscriptions are active, review Topic Policies and IAM permissions, inspect Filter Policies, check endpoint health, review CloudWatch delivery metrics, and examine CloudTrail logs for configuration or permission changes.

---

## 10. When should you use FIFO Topics?

**Answer**

FIFO Topics should be used when message ordering and exactly-once publishing are required, such as financial transactions, payment processing, inventory updates, and other business workflows where processing order is critical.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Design Topics around business events rather than applications.
- Use SNS + SQS for reliable event distribution.
- Keep subscribers independent and loosely coupled.
- Configure Filter Policies instead of creating unnecessary Topics.
- Encrypt every production Topic.
- Use customer-managed KMS keys for sensitive workloads.
- Monitor delivery failures continuously.
- Prefer HTTPS endpoints.
- Review Topic Policies regularly.
- Build idempotent downstream consumers.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Topics | `aws sns list-topics` |
| Create Topic | `aws sns create-topic` |
| Delete Topic | `aws sns delete-topic` |
| View Topic Attributes | `aws sns get-topic-attributes` |
| Subscribe Endpoint | `aws sns subscribe` |
| List Subscriptions | `aws sns list-subscriptions` |
| Publish Message | `aws sns publish` |
| Publish SMS | `aws sns publish --phone-number` |
| Unsubscribe | `aws sns unsubscribe` |

---

# Final Thoughts

Amazon SNS is one of the foundational messaging services in AWS and serves as the event distribution layer for modern cloud-native applications. Combined with Amazon SQS, AWS Lambda, EventBridge, CloudWatch, IAM, and AWS KMS, Amazon SNS enables scalable, secure, and loosely coupled event-driven architectures that are widely used in enterprise backend systems.

---
