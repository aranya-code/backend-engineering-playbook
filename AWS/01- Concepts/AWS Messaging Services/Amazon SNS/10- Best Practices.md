# Introduction

Amazon SNS is designed to be a highly available, scalable, and fully managed messaging service.

Although Amazon SNS requires minimal operational management, following AWS best practices is essential for building secure, reliable, and production-ready event-driven applications.

This chapter covers recommended practices for architecture, security, monitoring, scalability, and operational excellence.

---

# Design Topics Around Business Domains

Instead of creating a single topic for every application event, organize topics by business functionality.

Good Example

```
order-events

payment-events

inventory-events

shipping-events

user-notifications
```

Avoid

```
application-events
```

Using business-specific topics improves maintainability and simplifies access control.

---

# Keep Publishers and Subscribers Loosely Coupled

Publishers should only know about the SNS Topic.

```
Application

↓

SNS Topic

↓

Subscribers
```

Publishers should never directly invoke downstream services.

---

# Prefer SNS + SQS for Backend Processing

For reliable application processing, use Amazon SNS together with Amazon SQS.

```
Application

↓

Amazon SNS

↓

Amazon SQS

↓

Worker
```

Benefits include:

- Reliable message storage
- Independent scaling
- Retry support
- Dead Letter Queues

---

# Use Message Filtering

Avoid sending every message to every subscriber.

Instead, use Filter Policies.

```
SNS Topic

↓

Filter Policy

↓

Relevant Subscriber
```

Benefits:

- Lower processing costs
- Reduced network traffic
- Better scalability
- Simpler subscriber applications

---

# Separate Notification and Business Events

Keep user notifications separate from backend processing.

Good

```
order-events

user-notifications
```

Avoid mixing:

```
Orders

↓

Emails

↓

Payments

↓

Inventory

↓

SMS
```

Separate topics simplify maintenance.

---

# Enable Server-Side Encryption

Always encrypt production topics.

Use:

```
AWS KMS
```

Prefer:

```
alias/aws/sns
```

or

Customer Managed Keys for enterprise workloads.

---

# Apply the Principle of Least Privilege

Grant only required permissions.

Good

```
sns:Publish
```

Avoid

```
sns:*
```

Restrict:

- Publish
- Subscribe
- DeleteTopic
- SetTopicAttributes

---

# Use HTTPS Endpoints

Prefer HTTPS over HTTP.

```
SNS

↓

HTTPS

↓

Application
```

HTTPS protects messages during transmission.

---

# Monitor with CloudWatch

Monitor every production topic.

Recommended metrics:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- NumberOfNotificationsFilteredOut
- PublishSize

Configure CloudWatch Alarms for critical metrics.

---

# Enable CloudTrail

CloudTrail records all SNS API activity.

Monitor operations such as:

- Publish
- Subscribe
- DeleteTopic
- SetTopicAttributes

CloudTrail provides a complete audit trail.

---

# Create Separate Topics for Different Environments

Avoid sharing topics across environments.

Good

```
dev-order-events

test-order-events

prod-order-events
```

Benefits:

- Better isolation
- Reduced deployment risk
- Easier troubleshooting

---

# Keep Messages Small

SNS is designed for lightweight event notifications.

Instead of sending large payloads:

```
Upload File

↓

Amazon S3

↓

Publish Object Key
```

Example

```
{
    "bucket":"images",
    "key":"photo.jpg"
}
```

This improves performance and reduces bandwidth usage.

---

# Design Idempotent Subscribers

Subscribers should safely process duplicate messages.

```
Receive Event

↓

Already Processed?

↓

Yes

↓

Ignore
```

Idempotent consumers prevent duplicate business operations.

---

# Retry Transient Failures

Applications should distinguish between:

- Temporary failures
- Permanent failures

Retry temporary issues such as:

- Network interruptions
- External API timeouts
- Database connection failures

Avoid retrying permanent validation errors.

---

# Use Dead Letter Queues

When Amazon SNS delivers messages to Amazon SQS, configure a Dead Letter Queue (DLQ) for the queue.

```
SNS

↓

SQS

↓

Retry

↓

Dead Letter Queue
```

This prevents problematic messages from blocking normal processing.

---

# Use Meaningful Topic Names

Choose descriptive names.

Good

```
payment-events

inventory-updates

shipment-events
```

Avoid

```
topic1

events

test
```

Meaningful names simplify operations.

---

# Version Event Schemas

Business events evolve over time.

Include version information.

Example

```json
{
    "eventVersion": "1.0",
    "eventType": "OrderCreated"
}
```

Schema versioning enables backward compatibility.

---

# Monitor Subscriber Health

Monitor downstream services as well as SNS.

Examples:

- Lambda errors
- SQS queue depth
- HTTP response codes
- Email delivery failures

Healthy topics do not guarantee healthy subscribers.

---

# Implement Infrastructure as Code

Manage SNS resources using:

- CloudFormation
- Terraform
- AWS CDK

Avoid manually creating production topics.

Infrastructure as Code provides:

- Version control
- Repeatability
- Automated deployments

---

# Document Event Contracts

Every published event should have clear documentation.

Example

```
Event Name

↓

OrderCreated

↓

Fields

↓

orderId

customerId

timestamp
```

Documenting event schemas improves collaboration between teams.

---

# Real-World Architecture

```
                Order Service

                      │

                      ▼

               Amazon SNS Topic

      ┌───────────────┼────────────────┐

      ▼               ▼                ▼

 Inventory Queue  Billing Queue  Notification Queue

      │               │                │

      ▼               ▼                ▼

  Worker A        Worker B         Email Service

                      │

                      ▼

                 CloudWatch

                      │

                      ▼

                    Alarms
```

This architecture provides:

- Loose coupling
- Independent scaling
- Reliable processing
- Centralized monitoring

---

# Production Checklist

Before deploying Amazon SNS:

- ☐ Topics created
- ☐ Topic names follow naming standards
- ☐ IAM permissions reviewed
- ☐ Topic Policies validated
- ☐ Server-Side Encryption enabled
- ☐ HTTPS endpoints configured
- ☐ Message Filtering configured
- ☐ CloudWatch monitoring enabled
- ☐ CloudWatch alarms configured
- ☐ CloudTrail enabled
- ☐ Subscriber health validated
- ☐ Infrastructure as Code committed
- ☐ Event schemas documented

---

# Common Mistakes

## Creating One Topic for Every Event

Too many topics become difficult to manage.

Group events by business domain.

---

## Sending Large Payloads

SNS is intended for event notifications.

Store large files in Amazon S3.

---

## Ignoring Monitoring

Without CloudWatch alarms, delivery failures may go unnoticed.

---

## Publishing Sensitive Data

Avoid placing confidential information directly in event payloads.

Encrypt data when necessary.

---

## Overly Broad IAM Permissions

Restrict access to only the required SNS actions.

---

## Forgetting Subscriber Design

Subscribers should be:

- Idempotent
- Fault tolerant
- Independently scalable

---

# Summary

Building reliable event-driven systems with Amazon SNS requires more than simply creating topics and publishing messages. Following best practices such as designing business-focused topics, using SNS with Amazon SQS, enabling encryption, applying least-privilege access, monitoring with CloudWatch, documenting event schemas, and implementing Infrastructure as Code results in secure, scalable, and maintainable messaging architectures suitable for production environments.