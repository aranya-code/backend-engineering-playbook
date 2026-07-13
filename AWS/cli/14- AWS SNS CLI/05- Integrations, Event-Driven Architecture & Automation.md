# Integrations, Event-Driven Architecture & Automation

> Learn how Amazon SNS integrates with AWS services to build scalable, event-driven architectures. This chapter covers Amazon SNS integrations with Amazon SQS, AWS Lambda, Amazon EventBridge, Amazon CloudWatch, AWS Step Functions, Amazon ECS, Auto Scaling, and production automation workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Integrate Amazon SNS with AWS services
- Build event-driven architectures
- Configure SNS → SQS fan-out
- Trigger AWS Lambda
- Integrate CloudWatch alarms
- Automate workflows
- Build scalable microservices
- Design enterprise event pipelines

---

# Event-Driven Architecture

Amazon SNS enables asynchronous event-driven systems.

```text
Publisher

↓

Amazon SNS

↓

Subscribers

↓

Processing
```

Publishers never wait for subscribers to finish.

---

# Common AWS Integrations

Amazon SNS integrates with:

```text
Amazon SNS

│

├── Amazon SQS

├── AWS Lambda

├── Amazon EventBridge

├── Amazon CloudWatch

├── AWS Step Functions

├── Amazon ECS

├── Amazon EC2

└── Auto Scaling
```

---

# SNS + Amazon SQS

The most common production architecture.

```text
Application

↓

Amazon SNS

│

├── Orders Queue

├── Billing Queue

├── Inventory Queue

└── Analytics Queue
```

Each queue processes events independently.

---

# Why SNS + SQS?

Benefits:

- Reliable message delivery
- Independent scaling
- Fault isolation
- Message persistence
- Loose coupling

---

# SNS → SQS Workflow

```text
Application

↓

Amazon SNS

↓

Amazon SQS

↓

Workers

↓

Database
```

Messages remain safely stored until processed.

---

# Subscribe an SQS Queue

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol sqs \
--notification-endpoint QUEUE_ARN
```

---

# SNS + Lambda

SNS can invoke Lambda functions automatically.

Architecture:

```text
Amazon SNS

↓

Lambda

↓

Processing
```

Ideal for:

- Image processing
- Notifications
- Event processing
- Serverless APIs

---

# Subscribe Lambda

```bash
aws sns subscribe \
--topic-arn TOPIC_ARN \
--protocol lambda \
--notification-endpoint LAMBDA_ARN
```

---

# Lambda Workflow

```text
Publish Event

↓

Amazon SNS

↓

Lambda

↓

Business Logic
```

Lambda scales automatically.

---

# SNS + EventBridge

Amazon SNS and EventBridge complement each other.

```text
Application

↓

Amazon SNS

↓

EventBridge

↓

Automation
```

Common use cases:

- Event routing
- Business workflows
- Event filtering

---

# SNS + CloudWatch

CloudWatch Alarms can publish notifications.

Architecture:

```text
CloudWatch Alarm

↓

Amazon SNS

↓

Email

↓

Operations Team
```

---

# CloudWatch Alarm Workflow

```text
CPU > 80%

↓

Alarm

↓

Amazon SNS

↓

Email

↓

Engineer
```

Widely used in production monitoring.

---

# SNS + Auto Scaling

Auto Scaling notifications can be delivered through SNS.

Example:

```text
Scale Out

↓

Amazon SNS

↓

Operations Team
```

Useful for infrastructure monitoring.

---

# SNS + Step Functions

Step Functions can publish notifications.

```text
Workflow

↓

Amazon SNS

↓

Subscribers
```

Common scenarios:

- Workflow completion
- Failure alerts
- Approval notifications

---

# SNS + ECS

Containerized applications can publish events.

```text
Amazon ECS

↓

Amazon SNS

↓

Amazon SQS
```

Microservices communicate asynchronously.

---

# SNS + EC2

Traditional applications can publish notifications.

```text
EC2

↓

Amazon SNS

↓

Subscribers
```

No infrastructure changes are required.

---

# SNS + Email

Email notifications remain one of the most common use cases.

```text
Application

↓

Amazon SNS

↓

Email

↓

Customer
```

Examples:

- Order confirmation
- Password reset
- Account alerts

---

# SNS + SMS

SMS is commonly used for:

- OTP verification
- Security alerts
- Emergency notifications

Workflow:

```text
Application

↓

Amazon SNS

↓

SMS
```

---

# Enterprise Fan-Out

```text
Order Service

↓

Amazon SNS

│

├── Billing Queue

├── Shipping Queue

├── Inventory Queue

├── Analytics Queue

└── Customer Notification
```

Each downstream service owns its own processing.

---

# Event Notification Workflow

```text
Business Event

↓

Amazon SNS

↓

Subscribers

↓

Business Processing
```

---

# Monitoring Workflow

```text
Application

↓

CloudWatch

↓

Alarm

↓

Amazon SNS

↓

Operations Team
```

SNS becomes the notification layer.

---

# Automation Workflow

```text
AWS Event

↓

CloudWatch

↓

Amazon SNS

↓

Lambda

↓

Automation
```

Example:

- Restart service
- Scale infrastructure
- Send notification

---

# Microservices Architecture

```text
User

↓

API

↓

Order Service

↓

Amazon SNS

│

├── Billing Service

├── Shipping Service

├── Notification Service

├── Search Service

└── Analytics Service
```

No service depends directly on another.

---

# High Availability

```text
Application

↓

Amazon SNS

↓

Multiple Subscribers
```

If one subscriber fails:

```text
Other Subscribers

↓

Continue Processing
```

The failure is isolated.

---

# CloudWatch Metrics

Monitor:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- PublishSize
- SMSMonthToDateSpentUSD

---

# Common Integration Errors

## Lambda Not Invoked

Verify:

- Subscription
- Lambda permissions
- Topic ARN
- Region

---

## SQS Not Receiving Messages

Verify:

- Queue Policy
- Topic Policy
- Subscription
- Queue ARN

---

## Email Not Received

Verify:

- Subscription confirmation
- Spam folder
- Email endpoint

---

## HTTP Endpoint Failure

Verify:

- Endpoint availability
- HTTPS certificate
- Delivery Policy
- Network connectivity

---

## CloudWatch Alarm Not Sending

Verify:

- Alarm state
- SNS Topic
- Subscription
- IAM permissions

---

# Production Best Practices

- Use SNS + SQS for reliable asynchronous processing.
- Use Lambda for lightweight event handling.
- Configure CloudWatch alarms for operational visibility.
- Keep Topics business-event focused.
- Design services to be loosely coupled.
- Monitor failed deliveries.
- Use EventBridge for advanced event routing.
- Prefer HTTPS endpoints over HTTP.
- Encrypt Topics and Queues.
- Make downstream consumers idempotent.

---

# Real-World Workflow

```text
Customer Places Order

↓

Order Service

↓

Amazon SNS

│

├── Billing Queue

├── Inventory Queue

├── Shipping Queue

├── Customer Email

└── Analytics Lambda
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
      ├── Amazon EventBridge
      ├── HTTPS Endpoint
      ├── Email
      └── SMS
              │
              ▼
Business Services
```

Amazon SNS acts as the event distribution layer, allowing multiple independent applications and AWS services to react to business events without direct dependencies.

---

# Interview Note

### Question

**Why are Amazon SNS and Amazon SQS commonly used together?**

### Answer

Amazon SNS and Amazon SQS complement each other by combining **event broadcasting** with **reliable message processing**. SNS immediately pushes an event to multiple subscribers, while each subscribed SQS queue stores its copy of the message until it is processed by its own consumers. This architecture enables independent scaling, fault isolation, retries, and loose coupling between microservices, making it one of the most widely used messaging patterns in AWS.

---

# Key Takeaways

- Amazon SNS integrates natively with SQS, Lambda, CloudWatch, EventBridge, Step Functions, ECS, and EC2.
- SNS acts as the event distribution layer in event-driven architectures.
- SNS + SQS provides scalable, fault-tolerant fan-out messaging.
- CloudWatch uses SNS to notify operators of alarms and operational events.
- Lambda enables serverless event processing with SNS.
- Event-driven architectures improve scalability by reducing direct service dependencies.
- Production systems combine SNS, SQS, Lambda, monitoring, and automation to build resilient cloud-native applications.