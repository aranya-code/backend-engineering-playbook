# Topic Design Best Practices

## Overview

A Kafka topic is more than just a destination for messages—it represents a business event stream. Poor topic design can lead to scalability issues, operational complexity, difficult maintenance, and performance bottlenecks. Well-designed topics, on the other hand, make systems easier to understand, scale, and evolve.

Designing topics correctly is one of the most important architectural decisions in a Kafka-based system because changing topic structures later can be expensive and disruptive.

This chapter discusses the best practices for designing Kafka topics for production environments.

---

# Design Topics Around Business Domains

Topics should represent business events, not technical implementations.

Good examples:

```text
orders.created

orders.updated

payments.completed

inventory.reserved

shipment.delivered
```

Poor examples:

```text
topic1

events

queue

test

data
```

Business-oriented names make topics easier to understand.

---

# Think in Event Streams

A topic should represent a continuous stream of related events.

Example:

```text
orders.created

↓

Order Created Event

↓

Order Created Event

↓

Order Created Event
```

Every message belongs to the same business domain.

---

# One Business Domain Per Topic

Avoid mixing unrelated business events.

Bad:

```text
application-events

↓

Orders

Payments

Invoices

Customers
```

Better:

```text
orders.events

payments.events

customers.events
```

Each topic should have a single responsibility.

---

# Use Consistent Naming Conventions

Follow a consistent naming strategy.

Example:

```text
domain.entity.event
```

Examples:

```text
orders.created

orders.cancelled

payments.completed

users.registered
```

Consistency improves discoverability.

---

# Use Lowercase Names

Recommended:

```text
orders.created
```

Avoid:

```text
OrdersCreated

Orders.Created

ORDERS
```

Lowercase naming is easier to maintain across teams.

---

# Avoid Special Characters

Recommended:

```text
orders.created
```

Avoid:

```text
orders@created

orders#created

orders created
```

Stick to:

- Lowercase letters
- Numbers
- Dots (`.`)
- Hyphens (`-`)
- Underscores (`_`) if needed

---

# Event Naming

Event names should describe something that has already happened.

Good:

```text
Order Created

Payment Completed

Invoice Generated
```

Bad:

```text
Create Order

Generate Invoice

Update Payment
```

Events describe facts, not commands.

---

# Separate Commands from Events

Commands:

```text
Create Order
```

Events:

```text
Order Created
```

Kafka topics should generally contain events rather than commands.

---

# Topic Granularity

Decide whether to use:

One topic per event:

```text
orders.created

orders.updated

orders.cancelled
```

Or:

One topic per domain:

```text
orders.events
```

Both approaches are valid.

Choose based on:

- Consumer requirements
- Event volume
- Operational simplicity

---

# Event Size

Keep messages reasonably small.

Preferred:

```text
Customer ID

Order ID

Status
```

Avoid:

```text
Large Images

PDF Files

Videos
```

Store large files elsewhere and send references through Kafka.

---

# Message Keys

Use meaningful keys.

Example:

```text
Order ID
```

Benefits:

- Ordering
- Partition consistency
- Better scalability

Avoid random keys when ordering matters.

---

# Partition Strategy

Partition count should be planned carefully.

Consider:

- Consumer parallelism
- Future growth
- Throughput
- Ordering requirements

Avoid creating partitions without understanding workload characteristics.

---

# Avoid Too Few Partitions

Example:

```text
Orders

↓

1 Partition

↓

100 Consumers
```

Only one consumer can actively process messages.

---

# Avoid Too Many Partitions

Example:

```text
50 Topics

↓

500 Partitions Each
```

Result:

```text
25,000 Partitions
```

Too many partitions increase broker memory usage and operational overhead.

---

# Retention Policy

Choose retention according to business needs.

Examples:

```text
7 Days

30 Days

90 Days
```

Do not rely on default settings without reviewing requirements.

---

# Cleanup Policy

Delete:

```properties
cleanup.policy=delete
```

Compaction:

```properties
cleanup.policy=compact
```

Choose the policy based on the use case.

---

# Schema Evolution

Messages evolve over time.

Version schemas carefully.

Example:

Version 1:

```json
{
  "orderId": 101
}
```

Version 2:

```json
{
  "orderId": 101,
  "customerId": 55
}
```

Maintain backward compatibility whenever possible.

---

# Use Schema Registry

A Schema Registry provides:

- Version control
- Compatibility validation
- Schema sharing
- Safer deployments

Strongly recommended for production environments.

---

# Topic Ownership

Every topic should have a clearly defined owner.

Example:

```text
Orders Team

↓

orders.events
```

Ownership helps with:

- Maintenance
- Schema changes
- Incident response

---

# Documentation

Document every topic.

Include:

- Purpose
- Producer
- Consumers
- Schema
- Retention
- Partitions
- Replication Factor

Well-documented topics are easier to maintain.

---

# Avoid Test Topics in Production

Bad:

```text
test

demo

temp

new-topic
```

Remove temporary topics before production deployment.

---

# Multi-Team Environments

Use domain separation.

Example:

```text
finance.*

inventory.*

shipping.*

analytics.*
```

This improves organization and simplifies permission management.

---

# Topic Lifecycle

Every topic should have a lifecycle.

```text
Design

↓

Create

↓

Use

↓

Monitor

↓

Retire
```

Unused topics should be removed after validation.

---

# Example Architecture

```text
                 Producers
                     │
                     ▼
      ┌──────────────────────────┐
      │      Kafka Topics        │
      ├──────────────────────────┤
      │ orders.created           │
      │ orders.updated           │
      │ payments.completed       │
      │ inventory.reserved       │
      │ shipment.delivered       │
      └──────────────────────────┘
                     │
                     ▼
                Consumers
```

Each topic represents a clear business event stream.

---

# Good Topic Examples

```text
orders.created

orders.updated

orders.cancelled

payments.completed

customers.registered

inventory.updated

shipment.delivered
```

These names are descriptive and business-focused.

---

# Poor Topic Examples

```text
topic1

events

queue

data

messages

test

abc
```

These names provide little context.

---

# Advantages of Good Topic Design

- Easier maintenance
- Better scalability
- Clear ownership
- Simpler monitoring
- Easier onboarding
- Improved documentation
- Better security management
- Cleaner architecture

---

# Common Mistakes

- Mixing unrelated events in one topic.
- Using vague topic names.
- Creating too many partitions without planning.
- Using one topic for the entire application.
- Sending large binary files through Kafka.
- Ignoring schema evolution.
- Using random partition keys.
- Creating temporary topics in production.

---

# Best Practices

- Design topics around business domains.
- Use meaningful, consistent naming conventions.
- Keep messages small.
- Choose appropriate partition counts.
- Use meaningful message keys.
- Plan retention and cleanup policies.
- Version schemas carefully.
- Use a Schema Registry.
- Assign topic ownership.
- Document every production topic.

---

# Summary

Topic design has a significant impact on the scalability, maintainability, and reliability of a Kafka deployment. Well-designed topics are organized around business domains, follow consistent naming conventions, use appropriate partitioning strategies, and support schema evolution. By carefully planning topic structure, retention policies, ownership, and documentation, organizations can build Kafka platforms that remain easy to operate and evolve as business requirements change.

---

# Key Takeaways

- Design topics around business domains rather than technical implementations.
- Use consistent, descriptive naming conventions.
- Keep topics focused on a single business responsibility.
- Plan partition counts based on throughput and scalability.
- Use meaningful message keys to preserve ordering where needed.
- Configure retention and cleanup policies according to business requirements.
- Version schemas carefully and use a Schema Registry.
- Good topic design is a foundational practice for production-grade Kafka systems.