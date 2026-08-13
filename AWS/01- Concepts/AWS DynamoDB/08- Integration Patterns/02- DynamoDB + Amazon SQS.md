# 02 - DynamoDB + Amazon SQS

## Overview

Amazon DynamoDB and Amazon SQS are commonly integrated to build **resilient, asynchronous, and highly scalable distributed systems**.

DynamoDB provides durable storage, while Amazon SQS acts as a reliable message buffer that decouples services.

Instead of performing expensive business operations during an API request, applications can store data in DynamoDB and delegate background processing to workers through SQS.

This architecture improves:

- Scalability
- Fault tolerance
- Availability
- Reliability
- Throughput
- User experience

It is one of the most common production patterns used in microservices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why DynamoDB and SQS are used together
- Common integration architectures
- Asynchronous processing
- Event-driven workflows
- Reliability patterns
- Failure recovery
- Idempotency
- Dead Letter Queues (DLQs)
- Production best practices
- Interview questions

---

# Why Combine DynamoDB and SQS?

Without SQS:

```text
Client

↓

API

↓

Write to DynamoDB

↓

Generate Invoice

↓

Send Email

↓

Update Analytics

↓

Notify Warehouse

↓

Return Response
```

The client waits until everything finishes.

---

With SQS:

```text
Client

↓

API

↓

Write to DynamoDB

↓

Send Message to SQS

↓

Return Response

────────────

Worker

↓

Read Message

↓

Generate Invoice

↓

Send Email

↓

Analytics

↓

Warehouse
```

The API responds quickly while background processing continues independently.

---

# High-Level Architecture

```text
              Client

                 │

                 ▼

            API Gateway

                 │

                 ▼

          Backend Service

                 │

        ┌────────┴────────┐

        ▼                 ▼

 DynamoDB Table      Amazon SQS

                           │

                           ▼

                      Worker Service

                           │

         ┌─────────────────┼─────────────────┐

         ▼                 ▼                 ▼

      Email          Billing Service     Analytics
```

---

# Common Use Cases

This integration is commonly used for:

- Order processing
- Email notifications
- Image processing
- Report generation
- Payment processing
- Inventory updates
- Audit logging
- Background jobs
- ETL pipelines

---

# Pattern 1 — Asynchronous Order Processing

Customer places an order.

```text
POST /orders

↓

Store Order

↓

DynamoDB

↓

Publish Message

↓

SQS

↓

Return Success
```

Worker services process the order asynchronously.

---

# Pattern 2 — Background Processing

Instead of:

```text
Upload File

↓

Resize Images

↓

Generate Thumbnails

↓

Store Metadata

↓

Return Response
```

Use:

```text
Upload File

↓

Store Metadata

↓

Queue Job

↓

Return Response

────────────

Worker

↓

Resize Images

↓

Generate Thumbnails
```

---

# Pattern 3 — Microservices

```text
Order Service

↓

DynamoDB

↓

SQS

↓

Inventory Service

↓

Billing Service

↓

Shipping Service
```

Services communicate asynchronously instead of calling each other directly.

---

# Pattern 4 — Batch Processing

```text
Import CSV

↓

Store Records

↓

Queue Messages

↓

Workers

↓

Validate Records

↓

Generate Reports
```

Large workloads become horizontally scalable.

---

# Message Flow

```text
Application

↓

Write Item

↓

Publish Message

↓

Amazon SQS

↓

Worker

↓

Business Logic

↓

Complete
```

---

# Should DynamoDB or SQS Come First?

Two common approaches exist.

## Option 1 (Most Common)

```text
Write to DynamoDB

↓

Publish Message
```

Advantages:

- Data is stored immediately.
- Worker can retrieve data later.
- Easier recovery.

---

## Option 2

```text
Publish Message

↓

Worker

↓

Write to DynamoDB
```

Used when:

- Queue is the primary source of work.
- Workers own persistence.

Choose based on business requirements.

---

# Handling Failures

Scenario:

```text
Save to DynamoDB

↓

Publish to SQS

↓

Network Failure
```

Potential problem:

The order exists in DynamoDB but no message reaches SQS.

Solutions include:

- Transactional Outbox Pattern
- Retry logic
- EventBridge
- DynamoDB Streams

---

# Transactional Outbox Pattern

Instead of publishing directly:

```text
Order Saved

↓

Outbox Table

↓

Worker

↓

Publish to SQS
```

Benefits:

- Reliable message delivery
- No lost events
- Easier recovery

This is a common enterprise pattern.

---

# Idempotency

SQS provides **at-least-once delivery**.

Workers may receive the same message more than once.

Example:

```text
Message

↓

Processed

↓

Timeout

↓

Delivered Again
```

Workers must safely handle duplicate processing.

Common techniques:

- Conditional writes
- Request IDs
- Processed message table

---

# Dead Letter Queues (DLQs)

Messages that repeatedly fail should not block processing.

```text
Amazon SQS

↓

Retry

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Benefits:

- Fault isolation
- Easier debugging
- Prevents infinite retry loops

---

# Visibility Timeout

When a worker receives a message:

```text
Message

↓

Invisible

↓

Worker Processing

↓

Delete Message
```

If processing fails:

```text
Visibility Timeout Expires

↓

Message Returns to Queue
```

Choose the timeout carefully based on processing duration.

---

# Scaling Workers

Multiple workers can process the same queue.

```text
Amazon SQS

        │

 ┌──────┼──────┐

 ▼      ▼      ▼

Worker Worker Worker
```

Benefits:

- Horizontal scalability
- Automatic load distribution
- Fault tolerance

---

# Monitoring

Monitor both DynamoDB and SQS.

## DynamoDB

- Read throttling
- Write throttling
- RCUs
- WCUs
- Latency

## SQS

- Queue depth
- Messages received
- Messages deleted
- Oldest message age
- DLQ size

---

# Production Architecture

```text
                   Users

                      │

                API Gateway

                      │

                      ▼

              Backend Service

          ┌───────────┴────────────┐

          ▼                        ▼

     DynamoDB                 Amazon SQS

                                      │

                    ┌─────────────────┼─────────────────┐

                    ▼                 ▼                 ▼

              Worker A          Worker B         Worker C

                    │

          ┌─────────┼─────────┐

          ▼         ▼         ▼

     Email      Inventory    Billing

                    │

                    ▼

              CloudWatch Logs
```

---

# Performance Considerations

To maximize throughput:

- Batch messages when appropriate.
- Scale consumers horizontally.
- Minimize message payload size.
- Store large payloads in DynamoDB or Amazon S3 instead of SQS.
- Configure visibility timeout correctly.
- Monitor queue depth continuously.

---

# Security Best Practices

- Encrypt SQS using AWS KMS.
- Use IAM least privilege.
- Enable CloudTrail.
- Restrict queue policies.
- Enable VPC endpoints if required.
- Validate all incoming messages.
- Never trust message payloads blindly.

---

# Best Practices

- Keep messages lightweight.
- Store large objects outside the queue.
- Design idempotent consumers.
- Configure Dead Letter Queues.
- Monitor queue depth.
- Retry using exponential backoff.
- Scale workers horizontally.
- Use FIFO queues only when strict ordering is required.

---

# Common Mistakes

## Performing Heavy Work Inside APIs

Slow:

```text
Request

↓

Business Logic

↓

Response
```

Better:

```text
Request

↓

Queue

↓

Response
```

---

## Ignoring Duplicate Messages

SQS may deliver messages more than once.

Always implement idempotency.

---

## No Dead Letter Queue

Without a DLQ:

```text
Failed Message

↓

Infinite Retry

↓

Blocked Processing
```

---

## Large Queue Messages

SQS should carry references rather than large datasets.

Example:

```text
OrderID

↓

Lookup

↓

DynamoDB
```

instead of embedding the entire order.

---

# Interview Notes

A common interview question is:

> **Why integrate DynamoDB with Amazon SQS?**

DynamoDB stores application data, while SQS enables asynchronous processing. This decouples services, improves scalability, reduces API latency, and increases fault tolerance.

---

Another common question is:

> **Why must SQS consumers be idempotent?**

Amazon SQS provides at-least-once delivery. A message can be delivered more than once, so consumers must safely handle duplicate processing without producing incorrect results.

---

Another common question is:

> **What is the purpose of a Dead Letter Queue?**

A Dead Letter Queue stores messages that repeatedly fail processing, preventing them from blocking normal queue operations and making debugging easier.

---

Another common question is:

> **What is the Transactional Outbox Pattern?**

The Transactional Outbox Pattern stores business events alongside application data in the database. A separate process publishes those events to SQS, ensuring reliable message delivery even if failures occur after the database transaction.

---

# Key Takeaways

- DynamoDB and Amazon SQS are commonly combined to build scalable asynchronous systems.
- SQS decouples producers and consumers, improving resilience and user experience.
- Use DynamoDB for durable storage and SQS for background processing.
- Design workers to be idempotent because SQS provides at-least-once message delivery.
- Configure Dead Letter Queues, retries, and monitoring for production reliability.
- Enterprise systems often use patterns such as the Transactional Outbox Pattern to ensure reliable event publication.