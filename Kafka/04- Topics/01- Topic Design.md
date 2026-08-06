# Topic Design

## Overview

A Kafka Topic is the fundamental abstraction used to organize and store streams of events. Every message produced to Kafka is written to a topic, and every consumer reads messages from one or more topics.

While creating a topic is technically simple, **designing topics correctly is one of the most important architectural decisions** in a Kafka-based system. A poorly designed topic can lead to scalability issues, uneven load distribution, excessive storage usage, and operational complexity.

This chapter explains how to design Kafka topics for scalability, maintainability, and long-term production use.

---

# What is a Topic?

A Topic is a named stream of records stored in Kafka.

Example:

```text
Orders Topic

↓

Order Created

↓

Order Updated

↓

Order Cancelled
```

Applications publish records to topics, and consumers subscribe to them.

---

# Topics as Event Streams

Unlike a traditional queue, a Kafka topic is an append-only event log.

```text
Offset

0

↓

1

↓

2

↓

3

↓

4
```

New records are always appended to the end.

Existing records are never modified.

---

# Why Topic Design Matters

A topic design determines:

- Application scalability
- Data organization
- Consumer parallelism
- Storage requirements
- Future maintenance

Poor topic design becomes increasingly difficult to change as systems grow.

---

# Topic Design Goals

A well-designed topic should provide:

- Clear business meaning
- Scalability
- Independent consumption
- Efficient storage
- Easy maintenance
- Long-term flexibility

---

# Topic Design Process

A typical design workflow is:

```text
Business Events

↓

Identify Domains

↓

Define Topics

↓

Choose Partitions

↓

Configure Retention

↓

Choose Replication

↓

Deploy
```

Topic design begins with understanding the business domain—not Kafka itself.

---

# Domain-Driven Topic Design

Topics should represent business domains.

Good examples:

```text
orders

payments

customers

inventory

shipments
```

Poor examples:

```text
topic1

events

messages

data

records
```

Business-oriented names make systems easier to understand.

---

# One Topic Per Event Type

A topic should represent a logical category of events.

Example:

```text
Orders Topic

↓

Order Created

Order Updated

Order Cancelled
```

Avoid mixing unrelated business events.

Bad example:

```text
Orders

Payments

Customers

Invoices

↓

One Topic
```

This creates unnecessary coupling.

---

# Event-Based Design

Think in terms of business events.

Instead of:

```text
Database Tables
```

Think:

```text
Customer Registered

↓

Order Created

↓

Payment Completed

↓

Invoice Generated
```

Kafka works best when events describe something that happened.

---

# Topic Granularity

Topics should not be too broad or too narrow.

Too Broad:

```text
BusinessEvents
```

Contains:

- Orders
- Payments
- Inventory
- Shipping
- Notifications

Problems:

- Large consumers
- Complex filtering
- Poor ownership

---

Too Narrow:

```text
OrderCreated

OrderUpdated

OrderCancelled

OrderApproved

OrderPacked

OrderDelivered
```

Problems:

- Too many topics
- Operational overhead
- Difficult management

---

Better:

```text
Orders
```

Containing:

```text
Order Created

Order Updated

Order Cancelled
```

---

# Topic Ownership

Each topic should have a clear owner.

Example:

```text
Orders Topic

↓

Order Service
```

Avoid multiple services owning the same topic.

Ownership improves:

- Governance
- Documentation
- Schema evolution

---

# Independent Consumers

Multiple applications should consume the same topic independently.

Example:

```text
Orders Topic

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service

↓

Fraud Detection
```

Each service maintains its own Consumer Group.

---

# Topic Versioning

Schemas evolve over time.

Instead of replacing existing topics:

```text
orders.v1

↓

orders.v2
```

Or use a schema registry with backward-compatible schema evolution.

Versioning strategies should be planned before production deployment.

---

# Topic Naming Principles

A good topic name should be:

- Meaningful
- Stable
- Predictable
- Lowercase
- Business-oriented

Example:

```text
orders

payments

inventory
```

Avoid:

```text
Topic1

KafkaTopic

Test

Data
```

Naming conventions are discussed in the next chapter.

---

# Topic Size Considerations

Topics may contain:

```text
Thousands

Millions

Billions

Trillions

of Records
```

Design topics with long-term growth in mind.

---

# Partition Planning

Every topic contains one or more partitions.

Example:

```text
Orders Topic

↓

Partition 0

Partition 1

Partition 2

Partition 3
```

The number of partitions affects:

- Parallelism
- Scalability
- Throughput

Partition strategy is covered in a dedicated chapter.

---

# Retention Planning

Before creating a topic, determine:

```text
Keep Data

↓

1 Day

7 Days

30 Days

Forever
```

Retention impacts:

- Storage
- Replay capability
- Recovery options

---

# Compacted vs Regular Topics

Kafka supports two primary topic types.

### Regular Topic

Messages expire after the retention period.

Example:

```text
Orders
```

---

### Compacted Topic

Latest record per key is retained.

Example:

```text
Customer Profiles

↓

Latest State
```

Compaction is discussed in a separate chapter.

---

# Multi-Tenant Topics

Some organizations share topics between tenants.

Example:

```text
Orders

↓

Tenant A

Tenant B

Tenant C
```

Usually implemented using:

- Message Keys
- Tenant IDs
- Headers

Separate topics are often easier to manage unless tenant counts are very large.

---

# Security Considerations

Topic design should also consider:

- Access control
- Encryption
- Sensitive data
- Regulatory requirements

Example:

```text
Payments

↓

Restricted Access
```

Not every application should consume every topic.

---

# Topic Design Architecture

```text
Business Domain
        │
        ▼
Identify Events
        │
        ▼
Create Topic
        │
        ▼
Choose Partitions
        │
        ▼
Configure Retention
        │
        ▼
Assign Producers
        │
        ▼
Assign Consumers
```

---

# Real-World Example

An e-commerce platform.

```text
orders

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service

↓

Notification Service
```

Another topic:

```text
payments

↓

Fraud Detection

↓

Accounting

↓

Reporting
```

Each topic represents a distinct business capability.

---

# Good Topic Design Example

```text
orders

payments

customers

inventory

shipments

notifications
```

Each topic has:

- Clear ownership
- Well-defined purpose
- Independent consumers

---

# Poor Topic Design Example

```text
events

↓

Everything
```

Contains:

- Orders
- Payments
- Inventory
- Customers
- Shipping

Problems:

- Difficult filtering
- High coupling
- Poor scalability

---

# Best Practices

- Design topics around business domains.
- Keep topic names meaningful and consistent.
- Avoid mixing unrelated events.
- Plan for future growth.
- Define topic ownership.
- Design for multiple independent consumers.
- Decide retention policies before production.
- Document every topic.

---

# Common Mistakes

- Creating generic topics like `events` or `data`.
- Designing topics around database tables instead of business events.
- Creating too many tiny topics.
- Mixing unrelated domains in one topic.
- Ignoring future scalability.
- Changing topic names frequently.
- Forgetting ownership and documentation.

---

# Summary

Topic design is one of the most important architectural decisions in Kafka. Well-designed topics organize events around business domains, support independent consumers, scale efficiently through partitions, and provide a solid foundation for long-term event-driven systems. By carefully considering naming, ownership, retention, partitioning, and future growth, engineers can build Kafka architectures that remain maintainable and scalable as applications evolve.

---

# Key Takeaways

- Topics are append-only streams of business events.
- Design topics around business domains rather than technical implementations.
- Keep topics focused but avoid excessive fragmentation.
- Plan partitioning, retention, and ownership from the beginning.
- Multiple consumer groups can independently consume the same topic.
- Choose meaningful and stable topic names.
- Design topics for future scalability and schema evolution.
- Good topic design simplifies maintenance and enables scalable event-driven architectures.