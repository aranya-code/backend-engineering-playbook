# Consumers

## Overview

A **Consumer** is a client application that reads messages from one or more Kafka topics. While producers are responsible for publishing events, consumers are responsible for processing those events.

Consumers enable event-driven architectures by allowing multiple applications to independently react to the same event without affecting one another.

For example, when an order is placed, multiple consumers can independently process the event to update inventory, send confirmation emails, generate invoices, and perform analytics.

---

# What is a Consumer?

A consumer is any application that subscribes to one or more Kafka topics and continuously reads new messages.

Examples include:

- Inventory Service
- Payment Service
- Email Service
- Shipping Service
- Analytics Platform
- Fraud Detection System
- Recommendation Engine
- Audit Logging Service

Unlike traditional messaging systems, Kafka consumers control **when** and **how** they read messages.

---

# Consumer Architecture

A high-level consumer architecture looks like this.

```text
Kafka Topic

      │

      ▼

Kafka Consumer

      │

      ▼

Business Logic

      │

      ▼

Database / API / Another System
```

Consumers continuously poll Kafka for new messages.

---

# Consumer Workflow

The lifecycle of a consumer is shown below.

```text
Subscribe to Topic

        │

        ▼

Poll Messages

        │

        ▼

Deserialize Messages

        │

        ▼

Process Messages

        │

        ▼

Commit Offset

        │

        ▼

Poll Again
```

This loop continues until the consumer shuts down.

---

# Real-World Example

Suppose a customer places an order.

```text
Order Service

      │

      ▼

orders Topic
```

Several consumers process the same event.

```text
orders Topic

     │

 ┌───┼───────────────┐
 ▼   ▼               ▼

Inventory       Shipping

Email Service   Analytics
```

Each consumer works independently.

---

# Subscribing to Topics

A consumer subscribes to one or more topics.

Example:

```text
Consumer

↓

orders
```

Or multiple topics.

```text
Consumer

↓

orders

payments

notifications
```

Kafka automatically delivers messages from subscribed topics.

---

# Polling Messages

Consumers do not receive messages automatically.

Instead, they repeatedly ask Kafka for new data.

This process is called **polling**.

```text
Consumer

↓

Poll

↓

Receive Messages

↓

Poll Again
```

Polling is the core operation performed by every Kafka consumer.

---

# Continuous Poll Loop

A Kafka consumer usually runs indefinitely.

```text
Start Consumer

↓

Poll

↓

Process

↓

Commit Offset

↓

Poll Again

↓

Repeat
```

This loop allows consumers to process events in real time.

---

# Message Deserialization

Kafka stores messages as bytes.

Consumers convert those bytes back into usable objects.

```text
Kafka Bytes

↓

Deserializer

↓

Python Object
```

Common deserializers include:

- String
- JSON
- Avro
- Protobuf

The serializer used by the producer should match the deserializer used by the consumer.

---

# Processing Messages

After deserialization, business logic executes.

Examples include:

- Save to database
- Send email
- Update inventory
- Generate invoice
- Trigger another event
- Call an external API

Example flow:

```text
Read Message

↓

Validate

↓

Business Logic

↓

Database Update

↓

Commit Offset
```

---

# Offset Management

Consumers keep track of processed messages using offsets.

```text
Partition

Offset 0

Offset 1

Offset 2

Offset 3

Offset 4
```

After successfully processing a message, the consumer records its current offset.

This allows it to resume processing after a restart.

---

# Auto Offset Commit

Kafka can automatically commit offsets.

```properties
enable.auto.commit=true
```

Workflow:

```text
Read

↓

Process

↓

Kafka Commits Offset
```

Advantages:

- Easy to configure
- Less application code

Disadvantages:

- May lose messages if processing fails before completion.

---

# Manual Offset Commit

In production systems, offsets are often committed manually.

```text
Read

↓

Validate

↓

Business Logic

↓

Database Commit

↓

Offset Commit
```

This ensures offsets are committed only after successful processing.

---

# Consumer Lag

Consumer lag is the difference between:

- The latest message in the partition.
- The last processed offset.

Example:

```text
Latest Offset

250

Consumer Offset

220

Lag = 30
```

Large consumer lag indicates the consumer cannot keep up with incoming messages.

---

# Consumer Scaling

Consumers are typically organized into consumer groups.

Example:

```text
Orders Topic

P0

P1

P2

P3

      │

Consumer Group

      │

 ┌──────────┐
 │Consumer 1│
 └──────────┘

 ┌──────────┐
 │Consumer 2│
 └──────────┘
```

Kafka automatically distributes partitions among consumers.

This allows applications to process data in parallel.

---

# Message Ordering

Kafka guarantees ordering only within a partition.

```text
Partition

Order 1

↓

Order 2

↓

Order 3
```

Consumers always process these messages in sequence.

Across different partitions, ordering is not guaranteed.

---

# Consumer Failures

Consumers may fail due to:

- Application crash
- Network failure
- Broker failure
- Timeout
- Database failure

Since Kafka stores offsets, consumers can recover and continue processing after restarting.

---

# Graceful Shutdown

A consumer should close cleanly before exiting.

```text
Receive Shutdown Signal

↓

Finish Processing

↓

Commit Offset

↓

Close Consumer
```

Graceful shutdown prevents duplicate processing and minimizes message loss.

---

# Consumer Configuration

Common consumer configuration options include:

| Configuration | Purpose |
|--------------|---------|
| bootstrap.servers | Kafka broker addresses |
| group.id | Consumer group identifier |
| enable.auto.commit | Automatic offset commits |
| auto.offset.reset | Start position for new consumers |
| max.poll.records | Maximum records returned per poll |
| session.timeout.ms | Consumer heartbeat timeout |
| fetch.min.bytes | Minimum data fetched in one request |

These settings directly affect performance and reliability.

---

# Best Practices

- Use consumer groups for scalability.
- Prefer manual offset commits for production systems.
- Handle processing failures gracefully.
- Monitor consumer lag regularly.
- Keep message processing idempotent.
- Close consumers gracefully.
- Match serializers and deserializers.
- Log processing failures.

---

# Common Mistakes

- Performing long-running work inside the poll loop.
- Ignoring consumer lag.
- Committing offsets before processing finishes.
- Using automatic commits for critical workflows.
- Forgetting graceful shutdown.
- Assuming ordering across partitions.
- Not handling deserialization errors.

---

# Summary

A Kafka consumer continuously reads messages from subscribed topics, processes them, and tracks its progress using offsets. By polling Kafka, deserializing messages, executing business logic, and committing offsets, consumers enable reliable and scalable event processing. Combined with consumer groups, Kafka consumers can process millions of events in parallel while maintaining fault tolerance and independent message consumption.

---

# Key Takeaways

- Consumers read messages from Kafka topics.
- Consumers continuously poll Kafka for new events.
- Messages must be deserialized before processing.
- Offsets track consumer progress.
- Manual offset commits provide greater reliability.
- Consumer lag measures processing delay.
- Consumer groups enable horizontal scaling.
- Ordering is guaranteed only within a partition.
- Graceful shutdown prevents duplicate processing.
- Proper consumer configuration is essential for building reliable event-driven systems.