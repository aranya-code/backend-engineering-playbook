# Topics

## Overview

A **Topic** is one of the fundamental building blocks of Apache Kafka. It is a logical category or stream where messages (events) are stored.

Every message produced to Kafka is written to a topic, and every consumer reads messages from one or more topics.

You can think of a topic as a continuously growing event stream that stores related events together.

For example:

- User registrations
- Orders
- Payments
- Notifications
- Logs

Each type of event is usually stored in its own topic.

---

# What is a Topic?

A topic is similar to a folder that groups related messages.

For example:

```text
Kafka Cluster

├── orders
├── payments
├── users
├── notifications
└── logs
```

Instead of storing all events together, Kafka organizes them into topics based on their purpose.

---

# Why Do We Need Topics?

Imagine an e-commerce application.

Without topics:

```text
Kafka

Order Created
Payment Completed
User Registered
Inventory Updated
Email Sent
Application Log
```

Every consumer would receive every type of event.

This creates unnecessary processing and makes the system difficult to scale.

With topics:

```text
Kafka

orders
payments
users
inventory
notifications
logs
```

Each service subscribes only to the topics it needs.

---

# Real-World Example

Consider an online shopping platform.

Different services are interested in different events.

```text
                Kafka

      ┌────────────────────┐
      │ orders             │
      │ payments           │
      │ inventory          │
      │ notifications      │
      │ analytics          │
      └────────────────────┘
```

Services consume only relevant topics.

```text
Order Service
      │
      ▼
orders Topic
      │
 ┌────┼──────────────┐
 ▼    ▼              ▼
Inventory      Shipping
Service         Service
```

Similarly,

```text
Payment Service
      │
      ▼
payments Topic
      │
 ┌────┼────────────┐
 ▼    ▼            ▼
Accounting Fraud Detection
```

This separation keeps systems loosely coupled.

---

# Topics are Logical, Not Physical

A topic is a logical abstraction.

Physically, Kafka stores data inside **partitions**.

For example:

```text
orders Topic

├── Partition 0
├── Partition 1
├── Partition 2
└── Partition 3
```

Applications interact with the topic.

Kafka internally decides which partition stores each message.

---

# Topic Lifecycle

A topic typically follows this lifecycle:

```text
Create Topic
      │
      ▼
Producer Publishes Events
      │
      ▼
Kafka Stores Events
      │
      ▼
Consumers Read Events
      │
      ▼
Retention Period Expires
      │
      ▼
Old Messages Removed
```

Unlike traditional queues, messages are not deleted immediately after consumption.

---

# Topic Naming

Kafka topic names should clearly describe the events they contain.

Good examples:

```text
orders

payments

inventory

notifications

user-events

audit-logs
```

Poor examples:

```text
topic1

test

demo

data

events

abc
```

A meaningful topic name improves readability and maintainability.

---

# Topic Naming Conventions

Most organizations define naming standards.

Examples:

```text
orders

payments

notifications

user-events

inventory-updates

audit-logs
```

For large systems:

```text
ecommerce.orders

ecommerce.payments

billing.invoices

user.profile

inventory.stock

analytics.events
```

Using namespaces helps organize topics across multiple teams.

---

# Topic Characteristics

Every topic has configurable properties.

Some of the most common include:

- Number of partitions
- Replication factor
- Retention period
- Cleanup policy
- Compression
- Maximum message size

These properties determine how Kafka stores and manages data.

---

# Number of Partitions

A topic can contain one or many partitions.

Example:

```text
orders

Partition 0

Partition 1

Partition 2

Partition 3
```

More partitions generally provide:

- Better scalability
- Higher throughput
- Parallel processing

Choosing the correct number of partitions is an important architectural decision.

---

# Replication Factor

Each partition can have multiple replicas.

Example:

```text
orders

Partition 0

Leader

Follower

Follower
```

A replication factor of three means each partition exists on three brokers.

Benefits:

- High availability
- Fault tolerance
- Data durability

---

# Retention Period

Kafka retains messages for a configurable period.

Example:

```text
Retention = 7 Days
```

Even after a consumer reads a message, Kafka keeps it until the retention policy expires.

Common retention settings:

- 24 hours
- 3 days
- 7 days
- 30 days

Some systems retain messages for several months.

---

# Topic Cleanup Policies

Kafka supports two cleanup strategies.

## Delete Policy

Old messages are removed after the retention period.

```text
Message

↓

Stored

↓

Retention Expires

↓

Deleted
```

This is the default behavior.

---

## Log Compaction

Kafka keeps the latest message for each unique key.

Example:

```text
User 101

Version 1

Version 2

Version 3
```

After compaction:

```text
User 101

Version 3
```

Log compaction is commonly used for:

- User profiles
- Configuration data
- Account information
- Product catalog updates

---

# Topic Creation

Topics can be created in several ways.

- Kafka CLI
- Admin APIs
- Kafka Admin Client
- Automatic topic creation (not recommended in production)

Example:

```bash
kafka-topics.sh \
--create \
--topic orders \
--partitions 3 \
--replication-factor 3
```

---

# Topic Deletion

Topics can also be deleted.

```bash
kafka-topics.sh \
--delete \
--topic orders
```

Deleting a topic permanently removes all stored messages.

This operation should be performed carefully.

---

# Topic Description

Kafka provides commands to inspect a topic.

Example:

```bash
kafka-topics.sh \
--describe \
--topic orders
```

The output typically includes:

- Partition count
- Replication factor
- Leader
- Replicas
- ISR
- Configuration

---

# Topic vs Queue

| Traditional Queue | Kafka Topic |
|-------------------|-------------|
| Message usually consumed once | Multiple consumers can read the same message |
| Message often deleted immediately | Message retained for configured duration |
| One consumer typically processes each message | Many consumer groups can process the same message |
| Limited replay capability | Supports replaying historical events |

---

# Topic Design Best Practices

Choose topic names based on business events rather than technical implementations.

Prefer:

```text
orders

payments

inventory

notifications
```

Avoid:

```text
queue1

service-data

misc

temp
```

Additional recommendations:

- Keep naming consistent.
- Avoid overly generic names.
- Separate unrelated events into different topics.
- Estimate partition requirements before production.
- Configure appropriate retention periods.
- Use replication for fault tolerance.

---

# Common Mistakes

- Using a single topic for every event.
- Creating too many small topics.
- Choosing poor topic names.
- Ignoring retention settings.
- Using automatic topic creation in production.
- Underestimating partition requirements.
- Deleting production topics accidentally.

---

# Summary

A topic is the logical container where Kafka stores related events. Producers publish messages to topics, while consumers subscribe to the topics they are interested in. Internally, Kafka stores topic data in partitions, enabling scalability and parallel processing. Proper topic design—including naming conventions, partition planning, replication, and retention policies—is essential for building reliable and maintainable event-driven systems.

---

# Key Takeaways

- A topic is a logical stream of related events.
- Producers write messages to topics.
- Consumers subscribe to topics.
- Topics are internally divided into partitions.
- Multiple consumer groups can independently read the same topic.
- Topic properties include partitions, replication factor, and retention.
- Meaningful topic names improve maintainability.
- Proper topic design is critical for scalability and long-term system reliability.