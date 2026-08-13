# Introduction to SNS CLI

> Learn how to build scalable, event-driven applications using **Amazon Simple Notification Service (Amazon SNS)** and the **AWS Command Line Interface (AWS CLI)**. This chapter introduces SNS architecture, Topics, Publishers, Subscribers, message delivery, fan-out messaging, and the core CLI commands required to manage production notification systems.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon SNS
- Understand publish-subscribe messaging
- Understand Topics
- Manage subscriptions
- Publish notifications
- Build event-driven architectures
- Manage SNS using AWS CLI

---

# Why Amazon SNS?

In a tightly coupled architecture:

```text
Application

↓

Email Service
```

The application waits for every notification to complete.

Amazon SNS decouples notification delivery.

```text
Application

↓

Amazon SNS

│

├── Email

├── SMS

├── Lambda

├── SQS

└── HTTP Endpoint
```

One published message can be delivered to multiple subscribers simultaneously.

---

# What is Amazon SNS?

Amazon Simple Notification Service (Amazon SNS) is AWS's fully managed **publish-subscribe (Pub/Sub)** messaging service.

Amazon SNS enables applications to:

- Publish events
- Notify multiple subscribers
- Fan out messages
- Trigger serverless workflows
- Build event-driven architectures

---

# Publish-Subscribe Model

Instead of communicating directly:

```text
Producer

↓

Consumer
```

Applications publish messages to a Topic.

```text
Producer

↓

SNS Topic

↓

Subscribers
```

Subscribers automatically receive notifications.

---

# SNS Architecture

```text
Publisher

↓

SNS Topic

↓

Subscribers
```

SNS acts as the messaging hub.

---

# Core Components

Amazon SNS consists of:

```text
Amazon SNS

│

├── Topic

├── Publisher

├── Subscriber

├── Subscription

└── Endpoint
```

---

# Publisher

A Publisher sends messages.

Examples:

- Backend API
- Lambda
- EventBridge
- ECS
- EC2

---

# Topic

A Topic acts as the communication channel.

Messages are published to Topics rather than individual consumers.

Example:

```text
Order Topic
```

Every subscriber receives the message.

---

# Subscriber

Subscribers receive notifications.

Supported subscriber types include:

- Amazon SQS
- AWS Lambda
- Email
- SMS
- HTTP
- HTTPS

---

# Subscription

A Subscription connects an endpoint to a Topic.

```text
Topic

↓

Subscription

↓

Endpoint
```

Multiple subscriptions may exist for one Topic.

---

# Endpoint

The destination receiving notifications.

Examples:

```text
Email

SMS

Lambda

SQS

HTTPS
```

---

# Fan-Out Messaging

Amazon SNS delivers a single message to multiple subscribers.

```text
Publisher

↓

Amazon SNS

│

├── Queue A

├── Queue B

├── Lambda

└── Email
```

Each subscriber receives an independent copy.

---

# Typical Workflow

```text
Order Created

↓

Amazon SNS

│

├── Inventory Service

├── Billing Service

├── Notification Service

└── Analytics Service
```

Each service processes the event independently.

---

# Amazon SNS CLI Namespace

Amazon SNS uses:

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

# Verify AWS Identity

```bash
aws sts get-caller-identity
```

---

# Create Topic

```bash
aws sns create-topic \
--name order-events
```

SNS returns:

```text
Topic ARN
```

---

# List Topics

```bash
aws sns list-topics
```

---

# View Topic Attributes

```bash
aws sns get-topic-attributes \
--topic-arn TOPIC_ARN
```

---

# Delete Topic

```bash
aws sns delete-topic \
--topic-arn TOPIC_ARN
```

Deleting a Topic also deletes its subscriptions.

---

# Publish a Message

```bash
aws sns publish \
--topic-arn TOPIC_ARN \
--message "Order Created"
```

All subscribers receive the notification.

---

# Production Workflow

```text
Client

↓

Backend API

↓

Amazon SNS

│

├── Email

├── SQS

├── Lambda

└── Monitoring
```

The backend publishes once, while Amazon SNS handles message distribution.

---

# Real-World Use Cases

Amazon SNS is commonly used for:

- Order notifications
- Payment events
- User registration
- Email alerts
- SMS alerts
- Fan-out messaging
- Microservices communication
- Monitoring alerts
- Incident notifications
- Event-driven workflows

---

# SNS vs SQS

| Amazon SNS | Amazon SQS |
|------------|------------|
| Pushes messages | Consumers pull messages |
| Pub/Sub model | Queue model |
| Fan-out messaging | Reliable buffering |
| Multiple subscribers | Single consumer workflow |

In production, SNS and SQS are often used together.

---

# SNS + SQS Architecture

```text
Application

↓

Amazon SNS

│

├── Order Queue

├── Billing Queue

├── Inventory Queue

└── Notification Queue
```

Each queue processes messages independently.

---

# Production Considerations

Before deploying Amazon SNS:

- Design Topics around business events.
- Use descriptive Topic names.
- Secure Topics using IAM.
- Enable encryption where appropriate.
- Monitor CloudWatch metrics.
- Configure delivery retries.
- Use SQS subscribers for reliable processing.

---

# Interview Note

### Question

**What is Amazon SNS and why is it used?**

### Answer

Amazon Simple Notification Service (Amazon SNS) is AWS's fully managed publish-subscribe messaging service that enables one publisher to deliver messages simultaneously to multiple subscribers. It is widely used for event-driven architectures, notifications, fan-out messaging, and decoupling distributed applications. Amazon SNS supports multiple subscriber types including Amazon SQS, AWS Lambda, HTTP/S endpoints, Email, and SMS.

---

# Key Takeaways

- Amazon SNS implements the publish-subscribe messaging pattern.
- Topics are the central communication channel.
- One published message can be delivered to multiple subscribers.
- SNS supports SQS, Lambda, Email, SMS, HTTP, and HTTPS endpoints.
- SNS is commonly paired with Amazon SQS to build reliable event-driven systems.
- The AWS CLI uses the `aws sns` namespace.
- Amazon SNS is a foundational service for modern microservices and cloud-native architectures.