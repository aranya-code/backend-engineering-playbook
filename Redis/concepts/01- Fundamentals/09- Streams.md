# Streams

## Overview

Redis Streams are an append-only data structure designed for handling continuous sequences of events. Unlike Lists, which simply store ordered values, Streams maintain an immutable log of events where every entry has a unique identifier.

Streams were introduced in Redis 5.0 to support event-driven architectures, messaging systems, audit logging, and real-time data processing. They combine the simplicity of Redis with messaging capabilities that are commonly found in dedicated event streaming platforms.

Unlike Pub/Sub, which delivers messages only to active subscribers, Streams retain messages until they are explicitly deleted, allowing consumers to process data at their own pace.

---

# What is a Redis Stream?

A Redis Stream is an append-only log of records.

Each record contains:

- A unique ID
- One or more field-value pairs

Conceptually:

```
orders

↓

+------------------------------+
| 1721848000000-0              |
| customer = Alice             |
| amount = 1500                |
+------------------------------+

+------------------------------+
| 1721848012000-0              |
| customer = Bob               |
| amount = 2200                |
+------------------------------+

+------------------------------+
| 1721848023000-0              |
| customer = Charlie           |
| amount = 950                 |
+------------------------------+
```

Each event is permanently ordered by its ID.

---

# Characteristics of Redis Streams

Redis Streams provide several powerful capabilities.

- Ordered event log
- Append-only
- Persistent messages
- Unique message IDs
- Multiple consumers
- Consumer groups
- Message acknowledgments
- Replay capability

These features make Streams suitable for reliable event processing.

---

# Stream Entry Structure

Each entry contains an automatically generated ID.

```
1657834200000-0

↓

Field

↓

Value

↓

Field

↓

Value
```

Example:

```
ID

↓

1721848000000-0

↓

customer

↓

Alice

↓

amount

↓

1500
```

Every event is uniquely identifiable.

---

# Internal Representation

Conceptually, a Stream behaves like an ever-growing event log.

```
Orders Stream

↓

Event 1

↓

Event 2

↓

Event 3

↓

Event 4

↓

Event 5
```

New events are always appended to the end.

Existing events are never modified.

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
| Add Event | O(1) |
| Read Event | O(N) |
| Range Query | O(log N + M) |
| Consumer Group Read | O(M) |

Streams are optimized for high-throughput event ingestion.

---

# Why Use Streams?

Suppose an e-commerce application receives new orders.

```
Customer Places Order

↓

Application

↓

Redis Stream

↓

Order Processor

↓

Payment Service

↓

Inventory Service
```

Each service can process the same event independently.

---

# Event Sourcing

Streams are ideal for event-driven architectures.

Example:

```
User Registered

↓

Email Service

↓

Analytics Service

↓

Audit Service

↓

Notification Service
```

The original event remains stored in the Stream.

New services can replay historical events if required.

---

# Order Processing

Every order becomes an event.

```
Order Created

↓

Redis Stream

↓

Payment

↓

Inventory

↓

Shipping
```

Each component processes the event independently.

---

# Activity Logging

Applications often record user activities.

```
User Login

↓

User Logout

↓

Password Change

↓

Profile Update
```

These events form a complete activity history.

---

# IoT Data Collection

IoT devices continuously generate events.

```
Sensor

↓

Temperature

↓

Humidity

↓

Pressure

↓

Battery
```

Redis Streams can efficiently store this continuous flow of data.

---

# Financial Transactions

Banking applications may record transaction events.

```
Deposit

↓

Withdrawal

↓

Transfer

↓

Balance Update
```

Each transaction remains available for auditing.

---

# Notification Systems

Notification services commonly use Streams.

```
Notification Created

↓

Email Worker

↓

SMS Worker

↓

Push Notification Worker
```

Each worker processes messages independently.

---

# Consumer Groups

One of the most powerful Stream features is Consumer Groups.

```
Redis Stream

↓

Consumer Group

↓

Worker A

Worker B

Worker C
```

Messages are automatically distributed among workers.

This improves scalability while preventing duplicate processing.

---

# Message Acknowledgment

Consumers acknowledge messages after successful processing.

```
Receive Event

↓

Process Event

↓

Acknowledge

↓

Completed
```

If a consumer fails before acknowledgment, another consumer can process the pending message.

This increases reliability.

---

# Streams vs Pub/Sub

| Feature | Streams | Pub/Sub |
|----------|----------|----------|
| Persistent Messages | Yes | No |
| Replay Messages | Yes | No |
| Consumer Groups | Yes | No |
| Acknowledgments | Yes | No |
| Offline Consumers | Supported | Not Supported |

Streams are generally preferred for reliable message processing.

---

# Streams vs Lists

| Feature | List | Stream |
|----------|------|---------|
| Ordered | Yes | Yes |
| Unique IDs | No | Yes |
| Consumer Groups | No | Yes |
| Message Replay | No | Yes |
| Acknowledgment | No | Yes |

Lists are suitable for simple queues.

Streams are designed for reliable event processing.

---

# Common Production Use Cases

Redis Streams are widely used for:

- Event-driven architectures
- Order processing
- Notification systems
- Background task processing
- Audit logging
- IoT telemetry
- Financial transaction logs
- Activity tracking
- Log aggregation
- Microservice communication

---

# When Should You Use Streams?

Choose Streams when:

- Events must be processed reliably.
- Multiple consumers need the same data.
- Messages should remain available after delivery.
- Replay capability is required.
- Consumer acknowledgments are important.

---

# When Should You Use Other Data Types?

| Requirement | Better Choice |
|-------------|---------------|
| Simple Queue | Lists |
| Publish Notifications Only | Pub/Sub |
| Object Storage | Hashes |
| Rankings | Sorted Sets |
| Cached Values | Strings |

Selecting the correct Redis data structure ensures better scalability and maintainability.

---

# Production Considerations

When using Streams in production:

- Remove processed messages periodically.
- Monitor Stream growth.
- Design idempotent consumers.
- Use Consumer Groups for scalable processing.
- Acknowledge messages only after successful processing.
- Monitor pending messages to detect stalled consumers.

---

# Best Practices

- Use Streams for event-driven systems.
- Prefer Consumer Groups for distributed workers.
- Keep event payloads concise.
- Use meaningful field names.
- Monitor memory usage for long-running Streams.
- Regularly archive or trim old events.

---

# Summary

Redis Streams provide a durable, append-only event log that supports reliable message processing, consumer groups, acknowledgments, and event replay. They bridge the gap between simple Redis data structures and dedicated event streaming systems, making them an excellent choice for modern backend applications that require scalable, event-driven architectures.

---

# Key Takeaways

- Redis Streams are append-only event logs.
- Every event receives a unique identifier.
- Streams support persistent message storage.
- Consumer Groups enable scalable message processing.
- Messages can be acknowledged and replayed.
- Streams are ideal for event sourcing, notifications, audit logs, and microservice communication.
- Compared to Lists and Pub/Sub, Streams provide significantly more reliability and flexibility for production systems.