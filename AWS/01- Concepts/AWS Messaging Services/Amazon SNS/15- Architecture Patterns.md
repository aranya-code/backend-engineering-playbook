# Introduction

Amazon SNS is one of the core building blocks of **event-driven architectures** on AWS.

Rather than tightly coupling applications together, Amazon SNS enables services to communicate through events.

This chapter explores the most common production architecture patterns that use Amazon SNS.

---

# Pattern 1 - Publish/Subscribe

The Publish/Subscribe (Pub/Sub) pattern is the fundamental architecture behind Amazon SNS.

```
Publisher

      │

      ▼

Amazon SNS Topic

      │

 ┌────┼──────────────┐

 ▼    ▼              ▼

SQS  Lambda       Email
```

A publisher sends one message.

Amazon SNS distributes it to every subscriber.

---

## Advantages

- Loose coupling
- Independent services
- Easy scaling
- High availability

---

## Common Use Cases

- Notifications
- Event broadcasting
- Microservices
- Monitoring

---

# Pattern 2 - Fan-Out Architecture

One event is distributed to multiple consumers.

```
                Order Service

                      │

                      ▼

                Amazon SNS Topic

       ┌──────────────┼──────────────┐

       ▼              ▼              ▼

 Inventory Queue  Billing Queue  Shipping Queue
```

Each subscriber receives an independent copy.

---

## Advantages

- Parallel processing
- Independent scaling
- Easy expansion

---

# Pattern 3 - SNS + SQS

This is the most common production architecture.

```
                Publisher

                    │

                    ▼

              Amazon SNS Topic

       ┌────────────┼────────────┐

       ▼            ▼            ▼

    SQS A        SQS B        SQS C

       │            │            │

       ▼            ▼            ▼

 Service A     Service B     Service C
```

SNS distributes messages.

SQS stores them until processed.

---

## Benefits

- Reliable delivery
- Retry support
- Dead Letter Queues
- Independent consumers

---

# Pattern 4 - SNS + Lambda

SNS directly invokes Lambda functions.

```
Publisher

↓

SNS Topic

↓

Lambda Function

↓

Business Logic
```

Useful for:

- Serverless processing
- Event transformation
- Image processing
- Data validation

---

# Pattern 5 - Event-Driven Microservices

Microservices communicate through events rather than direct API calls.

```
Order Service

↓

SNS Topic

↓

Inventory Service

↓

Billing Service

↓

Shipping Service
```

No service depends directly on another.

---

## Advantages

- Loose coupling
- Independent deployment
- Easier maintenance

---

# Pattern 6 - Notification System

Amazon SNS is commonly used to notify users through multiple channels.

```
Application

↓

SNS

↓

Email

↓

SMS

↓

Mobile Push
```

Examples

- Banking alerts
- OTP notifications
- Marketing campaigns
- Security alerts

---

# Pattern 7 - CloudWatch Alarm Notifications

CloudWatch can publish alarms directly to Amazon SNS.

```
CloudWatch Alarm

↓

Amazon SNS

↓

Email

↓

SMS

↓

Slack Webhook
```

Useful for:

- CPU alarms
- Disk alerts
- Database failures
- Security incidents

---

# Pattern 8 - Amazon S3 Event Processing

Amazon S3 publishes object events to Amazon SNS.

```
Amazon S3

↓

Object Created

↓

Amazon SNS

↓

Lambda

↓

Image Processing
```

Common events:

- Object Created
- Object Deleted
- Object Restored

---

# Pattern 9 - CI/CD Notifications

AWS deployment services publish pipeline events.

```
CodePipeline

↓

Amazon SNS

↓

Email

↓

Microsoft Teams

↓

Slack
```

Teams receive deployment notifications automatically.

---

# Pattern 10 - Auto Scaling Notifications

Auto Scaling publishes lifecycle events.

```
Auto Scaling

↓

Amazon SNS

↓

Operations Team
```

Useful for:

- Instance launch
- Instance termination
- Scaling events

---

# Pattern 11 - Cross-Account Event Distribution

Multiple AWS accounts communicate through SNS.

```
AWS Account A

↓

SNS Topic

↓

Topic Policy

↓

AWS Account B
```

Useful for:

- Multi-account organizations
- Centralized monitoring
- Shared services

---

# Pattern 12 - Multi-Region Notifications

Applications deployed across multiple Regions publish notifications independently.

```
US-East

↓

SNS

↓

Email

----------------

EU-West

↓

SNS

↓

Email
```

Improves regional isolation.

---

# Pattern 13 - Enterprise Event Bus

Large organizations organize events by business domains.

```
Sales

↓

Sales Topic

----------------

Payments

↓

Payment Topic

----------------

Inventory

↓

Inventory Topic
```

Each department owns its own topic.

---

# Pattern 14 - Audit Logging

Applications publish audit events.

```
Application

↓

SNS

↓

Audit Queue

↓

Archive

↓

Analytics
```

Useful for:

- Compliance
- Security
- Monitoring

---

# Pattern 15 - Serverless Event Processing

```
Amazon S3

↓

SNS

↓

Lambda

↓

DynamoDB

↓

CloudWatch
```

No servers required.

Entire workflow scales automatically.

---

# Choosing the Right Architecture

| Requirement | Recommended Pattern |
|-------------|---------------------|
| Broadcast messages | Publish/Subscribe |
| Reliable processing | SNS + SQS |
| Serverless workloads | SNS + Lambda |
| Multiple microservices | Event-Driven Architecture |
| User notifications | Notification System |
| Infrastructure alerts | CloudWatch + SNS |
| File processing | S3 + SNS |
| CI/CD alerts | CodePipeline + SNS |
| Cross-account messaging | Topic Policies |
| Enterprise events | Domain-based Topics |

---

# Architecture Decision Tree

```
Need to notify multiple systems?

        │

       Yes

        │

        ▼

Need reliable processing?

        │

 ┌──────┴──────┐

 │             │

Yes           No

 │             │

 ▼             ▼

SNS+SQS      SNS

                │

                ▼

Need serverless?

        │

 ┌──────┴──────┐

 │             │

Yes           No

 │             │

 ▼             ▼

Lambda      HTTP/SQS
```

---

# Real-World E-Commerce Architecture

```
Customer

↓

Order API

↓

Amazon SNS

↓

Inventory Queue

↓

Billing Queue

↓

Shipping Queue

↓

Notification Queue

↓

Analytics Queue

↓

CloudWatch
```

Every service processes the same business event independently.

---

# Best Practices

- Use SNS to broadcast business events.
- Use SNS + SQS for durable processing.
- Organize topics by business domain.
- Use Message Filtering to reduce unnecessary deliveries.
- Secure topics using IAM and Topic Policies.
- Monitor message delivery with CloudWatch.
- Enable encryption for production topics.
- Prefer event-driven communication over synchronous API calls.

---

# Common Mistakes

## Using SNS as a Queue

Amazon SNS distributes messages but does not store them.

---

## Creating One Topic for Every Application

Organize topics by business functionality rather than by application.

---

## Broadcasting Every Event

Publish only meaningful business events.

---

## Tight Coupling Through APIs

Avoid replacing asynchronous event-driven communication with direct service-to-service API calls when loose coupling is more appropriate.

---

## Ignoring Subscriber Failures

Monitor downstream subscribers such as SQS queues, Lambda functions, and HTTP endpoints.

---

# Summary

Amazon SNS enables a wide variety of architectural patterns, from simple publish/subscribe messaging to large-scale event-driven systems. By combining SNS with services such as Amazon SQS, AWS Lambda, Amazon S3, CloudWatch, and CodePipeline, organizations can build scalable, loosely coupled, highly available, and fault-tolerant applications. Choosing the appropriate architecture pattern depends on the application's reliability, scalability, and communication requirements.