# Introduction to SQS CLI

> Learn how to build reliable, scalable, and decoupled distributed systems using **Amazon Simple Queue Service (Amazon SQS)** and the **AWS Command Line Interface (AWS CLI)**. This chapter introduces SQS architecture, Standard and FIFO queues, message lifecycle, queue operations, and the core CLI commands required to manage production message queues.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon SQS
- Understand asynchronous messaging
- Understand queue architecture
- Learn Standard and FIFO queues
- Manage queues using AWS CLI
- Understand message lifecycle
- Build a foundation for event-driven architectures

---

# Why Amazon SQS?

In tightly coupled applications:

```text
Service A

↓

Direct API Call

↓

Service B
```

If **Service B** becomes unavailable, **Service A** also fails.

Amazon SQS decouples services.

```text
Service A

↓

Amazon SQS

↓

Service B
```

Messages remain safely stored until they are processed.

---

# What is Amazon SQS?

Amazon Simple Queue Service (Amazon SQS) is AWS's fully managed message queue service.

It enables applications to:

- Send messages
- Store messages
- Process messages asynchronously
- Scale independently
- Improve fault tolerance

---

# Why Use Message Queues?

Benefits include:

- Loose coupling
- Fault tolerance
- Scalability
- Reliability
- Load leveling
- Retry capability

Instead of processing requests immediately, applications can process them when resources become available.

---

# SQS Architecture

```text
Producer

↓

Amazon SQS

↓

Consumer
```

The producer sends messages.

The consumer retrieves and processes messages.

---

# Core Components

Amazon SQS consists of:

```text
Amazon SQS

│

├── Queue

├── Messages

├── Producer

├── Consumer

└── Dead Letter Queue
```

---

# Queue

A Queue stores messages until a consumer retrieves them.

Example:

```text
Order Queue

↓

Message 1

↓

Message 2

↓

Message 3
```

---

# Producer

A Producer sends messages.

Examples:

- Backend API
- Lambda
- ECS
- EC2
- EventBridge

---

# Consumer

A Consumer retrieves messages.

Examples:

- Lambda
- ECS Service
- EC2 Worker
- Kubernetes Pod
- Batch Job

---

# Message

A Message contains:

- Payload
- Metadata
- Message ID
- Timestamp

Example:

```json
{
    "orderId": 12345,
    "status": "created"
}
```

---

# Standard Queue

Characteristics:

- Nearly unlimited throughput
- Best-effort ordering
- At-least-once delivery

Architecture:

```text
Producer

↓

Standard Queue

↓

Multiple Consumers
```

---

# FIFO Queue

FIFO stands for:

```text
First In

↓

First Out
```

Characteristics:

- Strict ordering
- Exactly-once processing
- Lower throughput

---

# Standard vs FIFO

| Feature | Standard | FIFO |
|----------|----------|------|
| Ordering | Best Effort | Guaranteed |
| Delivery | At Least Once | Exactly Once |
| Throughput | Very High | Lower |
| Use Case | General Messaging | Financial, Payments, Inventory |

---

# Message Lifecycle

Every message follows this lifecycle:

```text
Producer

↓

Queue

↓

Consumer

↓

Delete
```

If the consumer fails before deleting the message:

```text
Queue

↓

Visibility Timeout Ends

↓

Available Again
```

---

# Queue URL

Every queue has a unique URL.

Example:

```text
https://sqs.ap-south-1.amazonaws.com/123456789012/orders
```

Most CLI operations require the Queue URL.

---

# Amazon SQS CLI Namespace

Amazon SQS uses:

```bash
aws sqs <operation>
```

Examples:

```bash
aws sqs list-queues
```

```bash
aws sqs create-queue
```

```bash
aws sqs send-message
```

---

# Verify AWS Identity

```bash
aws sts get-caller-identity
```

---

# List Queues

```bash
aws sqs list-queues
```

---

# Create Standard Queue

```bash
aws sqs create-queue \
--queue-name orders
```

---

# Create FIFO Queue

FIFO queues must end with:

```text
.fifo
```

Example:

```bash
aws sqs create-queue \
--queue-name orders.fifo \
--attributes FifoQueue=true
```

---

# Get Queue URL

```bash
aws sqs get-queue-url \
--queue-name orders
```

---

# Get Queue Attributes

```bash
aws sqs get-queue-attributes \
--queue-url QUEUE_URL \
--attribute-names All
```

---

# Delete Queue

```bash
aws sqs delete-queue \
--queue-url QUEUE_URL
```

---

# Typical Production Workflow

```text
Client

↓

Backend API

↓

Amazon SQS

↓

Worker

↓

Database
```

The API returns quickly while background workers process tasks asynchronously.

---

# Real-World Use Cases

Amazon SQS is commonly used for:

- Order processing
- Email sending
- Image processing
- Video transcoding
- Payment processing
- Log processing
- Report generation
- Background jobs
- Microservices communication

---

# Architecture Example

```text
User

↓

API Gateway

↓

Backend Service

↓

Amazon SQS

↓

Worker Service

↓

Amazon RDS
```

This architecture prevents backend APIs from blocking while long-running tasks execute.

---

# When Should You Use SQS?

Use Amazon SQS when:

- Tasks take a long time
- Systems need retries
- Services should be loosely coupled
- Consumers scale independently
- Background processing is required

Avoid using SQS for synchronous request-response communication.

---

# Common Queue Naming Strategy

Recommended:

```text
orders

payments

notifications

emails

image-processing
```

FIFO example:

```text
payments.fifo

inventory.fifo
```

---

# Production Considerations

Before deploying Amazon SQS:

- Choose Standard or FIFO appropriately.
- Design idempotent consumers.
- Configure retries.
- Plan for Dead Letter Queues.
- Enable encryption.
- Monitor CloudWatch metrics.
- Use IAM policies with least privilege.

---

# Interview Note

### Question

**What is Amazon SQS and why is it used?**

### Answer

Amazon Simple Queue Service (Amazon SQS) is AWS's fully managed message queue service that enables asynchronous communication between distributed applications. It decouples producers and consumers, improves fault tolerance, allows independent scaling, and provides reliable message delivery through Standard or FIFO queues.

---

# Key Takeaways

- Amazon SQS enables asynchronous communication.
- Queues decouple producers and consumers.
- Standard queues provide maximum throughput.
- FIFO queues guarantee ordering and exactly-once processing.
- Messages remain in the queue until successfully processed.
- The AWS CLI uses the `aws sqs` namespace.
- Amazon SQS is a foundational service for event-driven and microservices architectures.