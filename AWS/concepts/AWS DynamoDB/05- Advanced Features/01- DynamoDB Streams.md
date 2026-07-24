# 01 - DynamoDB Streams

## Overview

DynamoDB Streams is a change data capture (CDC) service that records **item-level modifications** made to a DynamoDB table.

Unlike a traditional database trigger, DynamoDB Streams is an **asynchronous event stream** that allows applications to react to data changes without affecting the performance of the original write operation.

Streams are the foundation for building:

- Event-driven architectures
- CQRS systems
- Real-time analytics
- Audit logging
- Search indexing
- Data replication
- Notification systems
- Serverless workflows

Rather than polling DynamoDB for changes, applications consume events directly from the stream.

---

# Why DynamoDB Streams Exist

Consider an e-commerce application.

When an order is created, multiple downstream systems need to react.

```text
Customer Places Order

↓

Order Saved
```

Now multiple services must update:

- Inventory
- Search Index
- Analytics
- Recommendation Engine
- Notification Service

Without Streams:

```text
Application

↓

Write Order

↓

Call Inventory

↓

Call Analytics

↓

Call Email

↓

Call Search
```

The application becomes tightly coupled.

With Streams:

```text
Write Order

↓

DynamoDB Streams

↓

Inventory

Analytics

Email

Search
```

Each consumer processes the event independently.

---

# Internal Architecture

```text
             Application

                    │

               PutItem

                    │

                    ▼

             DynamoDB Table

                    │

         Item Modification

                    │

                    ▼

            DynamoDB Streams

                    │

     ┌──────────────┼──────────────┐

     ▼              ▼              ▼

 Lambda      Kinesis Adapter    Custom Consumer

     ▼              ▼              ▼

 Downstream Systems & Services
```

Streams capture every modification without affecting the original write latency.

---

# What Events Are Captured?

Streams record:

```text
PutItem

UpdateItem

DeleteItem

TransactWriteItems
```

Each operation generates a stream record.

---

# Stream Record Lifecycle

```text
Write Request

↓

Commit to Table

↓

Create Stream Record

↓

Consumer Reads Event

↓

Process Event

↓

Checkpoint

↓

Expire
```

Stream records are retained for **24 hours**.

---

# Stream View Types

A stream can store different amounts of information.

| View Type | Contains |
|------------|-----------|
| KEYS_ONLY | Primary Keys only |
| NEW_IMAGE | Updated item |
| OLD_IMAGE | Previous item |
| NEW_AND_OLD_IMAGES | Before and after values |

Production systems commonly use:

```text
NEW_AND_OLD_IMAGES
```

for auditing and synchronization.

---

# Event Ordering

Ordering is guaranteed only within the same partition.

Example:

```text
Customer123

↓

Order1

↓

Order2

↓

Order3
```

Events arrive in order.

Across different partitions:

```text
CustomerA

CustomerB

CustomerC
```

Ordering is **not guaranteed**.

Applications should never assume global ordering.

---

# At-Least-Once Delivery

Streams provide:

```text
At-Least-Once Delivery
```

Meaning:

```text
Event

↓

Consumer

↓

Retry

↓

Same Event Again
```

Duplicate processing is possible.

Consumers must therefore be idempotent.

---

# Consumer Architecture

A common production architecture:

```text
           DynamoDB Streams

                  │

           Lambda Function

                  │

      ┌───────────┼───────────┐

      ▼           ▼           ▼

 Search      Notification   Analytics

    OpenSearch     SNS        Data Lake
```

Each consumer performs a single responsibility.

---

# Stream Processing Workflow

```text
Item Updated

↓

Stream Record Created

↓

Lambda Triggered

↓

Business Logic

↓

External Service Updated
```

The original database write completes before downstream processing begins.

---

# Retry Behavior

Suppose a Lambda function fails.

```text
Stream Event

↓

Lambda

↓

Failure

↓

Retry
```

The event remains available until:

- Successfully processed
- Stream retention expires

Applications should implement:

- Idempotency
- Dead-letter queues (DLQs)
- Monitoring

---

# Event Payload Example

A stream record may contain:

```text
Event Name

INSERT

MODIFY

REMOVE
```

Along with:

```text
Primary Key

Old Image

New Image

Timestamp
```

Consumers decide how to process the event.

---

# Streams vs Polling

| Feature | Polling | DynamoDB Streams |
|----------|----------|------------------|
| Real-Time | ❌ | ✅ |
| Efficient | ❌ | ✅ |
| Event Driven | ❌ | ✅ |
| Additional Reads | High | None |
| Low Latency | Poor | Excellent |

Streams eliminate the need for expensive polling.

---

# Streams vs Database Triggers

| Feature | Database Trigger | DynamoDB Streams |
|----------|------------------|------------------|
| Runs Inside Database | ✅ | ❌ |
| Asynchronous | Usually No | ✅ |
| Scales Independently | Limited | Excellent |
| Multiple Consumers | Difficult | Easy |

Streams support loosely coupled architectures.

---

# Real-World Example — Search Indexing

Customer updates a product.

```text
Product Updated

↓

DynamoDB Stream

↓

Lambda

↓

Update OpenSearch
```

Search results remain synchronized automatically.

---

# Real-World Example — Audit Logging

Employee updates payroll.

```text
Payroll Updated

↓

OLD_IMAGE

↓

NEW_IMAGE

↓

Audit Database
```

Every modification is preserved.

---

# Real-World Example — Cache Invalidation

Item modified.

```text
Update Product

↓

Stream Event

↓

Invalidate Redis

↓

Next Read

↓

Fresh Cache
```

Applications avoid stale cache entries.

---

# Real-World Example — Notifications

Order status changes.

```text
Status

↓

SHIPPED
```

Workflow:

```text
Stream Event

↓

Lambda

↓

SNS

↓

Customer Email
```

No notification logic exists inside the API.

---

# Real-World Example — Analytics

Every purchase generates:

```text
INSERT

↓

Stream

↓

Analytics Pipeline

↓

Dashboard
```

Business metrics update automatically.

---

# Performance Considerations

Streams introduce minimal overhead because:

- Writes complete before consumers execute.
- Consumers process asynchronously.
- Processing scales independently from the table.

However:

- Slow consumers increase processing lag.
- Long-running Lambda functions reduce throughput.
- Duplicate events require idempotent processing.

---

# Best Practices

- Keep stream consumers small and focused.
- Build idempotent processing logic.
- Enable DLQs for failed events.
- Monitor consumer lag using CloudWatch.
- Separate business responsibilities into independent consumers.
- Avoid performing long-running operations inside a single Lambda invocation.

---

# Common Mistakes

## Treating Streams as a Queue

Streams are intended for change data capture.

If guaranteed message ordering across unrelated entities or long-term message retention is required, services like Amazon SQS or Amazon Kinesis may be more appropriate.

---

## Assuming Exactly-Once Processing

Streams provide **at-least-once delivery**.

Consumers must safely handle duplicate events.

---

## Putting Too Much Logic in One Consumer

Poor:

```text
Lambda

↓

Inventory

↓

Email

↓

Billing

↓

Analytics

↓

Search
```

Better:

```text
One Event

↓

Multiple Independent Consumers
```

This improves scalability and fault isolation.

---

## Ignoring Failed Events

Production systems should monitor:

- Lambda failures
- Retry counts
- DLQ depth
- Stream processing lag

Ignoring failures can result in stale downstream systems.

---

# Architecture Perspective

```text
               DynamoDB Table

                      │

                Data Changed

                      │

              DynamoDB Streams

                      │

         ┌────────────┼────────────┐

         ▼            ▼            ▼

      Lambda      EventBridge   Custom App

         ▼            ▼            ▼

 Search Index   Notifications   Analytics
```

Streams decouple data persistence from downstream processing, enabling scalable event-driven architectures.

---

# Production Considerations

DynamoDB Streams are a core building block for modern event-driven systems.

Common production use cases include:

- CQRS read model updates
- Event sourcing
- Search indexing
- Cache invalidation
- Audit logging
- Notification systems
- Data lake ingestion
- Cross-service synchronization
- Machine learning pipelines

Successful production implementations emphasize:

- Idempotent consumers
- Independent processing pipelines
- Retry mechanisms
- Dead-letter queues
- Comprehensive monitoring

---

# Interview Notes

A common interview question is:

> **What is DynamoDB Streams?**

It is a change data capture service that records item-level modifications in a DynamoDB table and enables downstream systems to react asynchronously.

Another common question is:

> **Does enabling Streams slow down DynamoDB writes?**

No. Stream records are created after the write is committed, so consumer processing is asynchronous and does not block the original write.

Another common question is:

> **What delivery guarantee do DynamoDB Streams provide?**

Streams provide **at-least-once delivery**, so consumers must be idempotent because duplicate events may occur.

Another common question is:

> **When should DynamoDB Streams be used?**

Whenever changes to DynamoDB data need to trigger downstream processing, such as updating search indexes, sending notifications, invalidating caches, auditing changes, or feeding analytics pipelines.

---

# Key Takeaways

- DynamoDB Streams provide real-time change data capture for item-level modifications.
- Stream records are generated asynchronously after successful writes.
- Streams support event-driven architectures by decoupling producers from consumers.
- Ordering is guaranteed only within a partition, not globally.
- Delivery is **at least once**, so consumers must be idempotent.
- Streams integrate naturally with AWS Lambda, enabling scalable serverless processing.
- They are widely used for audit logging, cache invalidation, search indexing, CQRS, and analytics.