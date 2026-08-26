# 16 - Streams

## Overview

In traditional relational databases, applications often rely on **database triggers**, **Change Data Capture (CDC)**, or **transaction logs** to react whenever data changes.

For example:

- Send an email when an order is created.
- Update a search index after a product changes.
- Push notifications when a user updates their profile.
- Replicate data to another system.

DynamoDB follows a different approach.

Instead of triggers, DynamoDB provides **DynamoDB Streams**, a feature that captures every modification made to a table and exposes those changes as an ordered stream of events.

Applications can consume these events to build **event-driven architectures**, keeping downstream systems synchronized without modifying the primary application logic.

---

# What is a DynamoDB Stream?

A DynamoDB Stream is a **time-ordered sequence of item-level changes**.

Whenever an item is:

- Inserted
- Updated
- Deleted

DynamoDB records the event.

```text
Application

↓

DynamoDB Table

↓

Item Modified

↓

DynamoDB Stream

↓

Consumers
```

Unlike the table itself, the stream does not store the current state of the database—it stores **change events**.

---

# Why Streams Exist

Consider an online shopping application.

When an order is created, multiple actions should occur.

```text
Order Created

↓

Send Email

↓

Update Inventory

↓

Generate Invoice

↓

Notify Warehouse

↓

Update Analytics
```

Without Streams, the application would need to perform all these operations synchronously.

```text
Application

↓

Email

↓

Inventory

↓

Analytics

↓

Warehouse

↓

Invoice
```

As more integrations are added, the application becomes tightly coupled and harder to maintain.

With Streams:

```text
Application

↓

DynamoDB

↓

Stream

↓

Independent Consumers
```

Each consumer performs one responsibility independently.

---

# How Streams Work

Suppose a user updates their profile.

```text
User

↓

Update Profile

↓

DynamoDB

↓

Record Event

↓

Stream
```

The application completes its write operation immediately.

Later:

```text
Lambda

↓

Reads Stream

↓

Processes Event
```

This separation improves scalability and resilience.

---

# Stream Records

Each stream record contains information about the change.

Example:

```text
Operation

UPDATE
```

```text
Timestamp

2026-07-23T15:20:10Z
```

```text
Keys

USER#1001
```

Depending on configuration, the record may also include:

- Previous item
- Updated item
- Both versions

---

# Stream View Types

When enabling Streams, developers choose what information should be stored.

---

## 1. Keys Only

Stores only the primary key.

```text
PK

USER#1001
```

Useful when consumers only need to identify which item changed.

---

## 2. New Image

Stores the item **after** the modification.

```text
Before

Age = 25

↓

After

Age = 26
```

Only the updated version is available.

---

## 3. Old Image

Stores the item **before** modification.

Useful for:

- Auditing
- Logging
- Compliance

---

## 4. New and Old Images

Stores both versions.

```text
Old

Status = Pending

↓

New

Status = Approved
```

This option provides the richest information but produces larger stream records.

---

# Stream Retention

Stream records are not stored forever.

DynamoDB retains them for:

```text
24 Hours
```

After that period:

```text
Automatically Deleted
```

Streams are intended for near real-time processing rather than long-term storage.

---

# DynamoDB Streams Architecture

```text
                Client

                  │

                  ▼

            DynamoDB Table

                  │

        Item Insert / Update / Delete

                  │

                  ▼

          DynamoDB Stream

          │       │       │

          ▼       ▼       ▼

      Lambda   Analytics   Other Services
```

Multiple consumers can process the same stream independently.

---

# Streams and AWS Lambda

The most common integration is AWS Lambda.

```text
DynamoDB Table

↓

Stream

↓

Lambda Trigger

↓

Business Logic
```

Whenever an event appears:

- Lambda is invoked automatically.
- The changed record is passed as input.
- Business logic executes.

Example:

```text
User Registers

↓

Insert Item

↓

Stream Event

↓

Lambda

↓

Send Welcome Email
```

No polling is required.

---

# Event-Driven Architecture

Streams encourage an event-driven design.

Instead of:

```text
Application

↓

Email

↓

Analytics

↓

Search

↓

Notifications
```

Applications simply write to DynamoDB.

```text
Application

↓

DynamoDB
```

Everything else reacts asynchronously.

```text
Streams

↓

Email

↓

Analytics

↓

Search

↓

Warehouse
```

Each service evolves independently.

---

# Ordering Guarantees

Within a single partition key, DynamoDB Streams preserve the order of modifications.

Example:

```text
Balance = 100

↓

120

↓

150

↓

180
```

Consumers receive events in that same order for that partition key.

However, DynamoDB does **not** guarantee a global ordering across different partition keys because records are processed in parallel.

---

# Streams vs SQS

These services are often confused.

| Feature | DynamoDB Streams | Amazon SQS |
|----------|------------------|------------|
| Source | DynamoDB Changes | Any Producer |
| Triggered Automatically | ✅ Yes | ❌ No |
| Stores Database Events | ✅ Yes | ❌ No |
| Message Queue | ❌ No | ✅ Yes |
| Event Ordering | Per Partition Key | FIFO (FIFO Queues Only) |

Streams capture database changes.

SQS transports arbitrary application messages.

---

# Streams vs Kinesis

Another common comparison.

| Feature | DynamoDB Streams | Kinesis Data Streams |
|----------|------------------|----------------------|
| Purpose | Database Change Events | General Streaming Platform |
| Data Source | DynamoDB | Applications, IoT, Logs |
| Retention | 24 Hours | Configurable (up to 365 days) |
| Throughput | Managed by AWS | User Managed |
| Scaling | Automatic | Configurable |

Kinesis is a general-purpose streaming platform.

DynamoDB Streams are purpose-built for table modifications.

---

# Common Use Cases

Streams are commonly used for:

- Audit logging
- Event sourcing
- Search index synchronization
- Cache invalidation
- Notification systems
- Inventory updates
- Analytics pipelines
- Data replication
- CQRS architectures
- Lambda event processing

---

# Best Practices

- Keep stream-processing logic lightweight.
- Design consumers to be idempotent.
- Handle retries gracefully.
- Monitor Lambda failures and stream lag.
- Use dead-letter queues (DLQs) for failed processing.
- Process events asynchronously whenever possible.
- Separate business logic into independent consumers.

---

# Common Mistakes

## Performing Long-Running Operations

Stream consumers should finish quickly.

Lengthy processing delays subsequent records.

---

## Assuming Infinite Retention

Streams retain data for only 24 hours.

Consumers should process events promptly.

---

## Forgetting Idempotency

Consumers may occasionally process the same event more than once.

Business logic should safely handle duplicate processing.

---

## Treating Streams as a Message Queue

Streams represent database changes.

They are not intended to replace SQS, SNS, or EventBridge.

---

# Real-World Example

An online retailer stores orders in DynamoDB.

```text
Customer Places Order

↓

PutItem

↓

DynamoDB Table

↓

Stream Record Created
```

Multiple consumers react independently.

```text
Lambda A

↓

Send Confirmation Email
```

```text
Lambda B

↓

Reserve Inventory
```

```text
Lambda C

↓

Update Sales Dashboard
```

```text
Lambda D

↓

Notify Shipping Service
```

The order service remains simple while downstream systems evolve independently.

---

# Architecture Perspective

A modern event-driven AWS architecture often looks like this:

```text
Client

↓

API Gateway

↓

Lambda / ECS

↓

DynamoDB

↓

DynamoDB Streams

↓

Lambda

↓

SNS / SQS / EventBridge

↓

Microservices
```

The database becomes the source of truth, while Streams distribute changes throughout the ecosystem.

---

# Interview Notes

A common interview question is:

> **Why use DynamoDB Streams instead of calling multiple services directly after a database write?**

Because Streams decouple the application from downstream systems.

The application performs a single database write, while independent consumers react asynchronously. This reduces latency, improves fault isolation, and makes the system easier to extend as new integrations are added.

Another common question is:

> **Can DynamoDB Streams replace Kafka or Kinesis?**

No.

Streams are designed specifically to capture DynamoDB table changes. They are not general-purpose event streaming platforms and have a fixed 24-hour retention period. For broader event ingestion, log processing, or long-term streaming, services like Amazon Kinesis or Apache Kafka are more appropriate.

---

# Key Takeaways

- DynamoDB Streams capture item-level changes in near real time.
- Every insert, update, and delete can generate a stream record.
- Stream records can include keys, old images, new images, or both.
- Records are retained for 24 hours.
- Streams integrate seamlessly with AWS Lambda to build event-driven architectures.
- Ordering is guaranteed only within the same partition key.
- Streams complement services like Lambda, SNS, SQS, and EventBridge to build scalable, loosely coupled systems.