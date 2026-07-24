# Stream Commands

## Overview

Redis Streams are an **append-only log data structure** introduced in Redis 5.0. They were designed to support high-throughput event streaming, message queues, and event-driven architectures.

Unlike Pub/Sub, where messages disappear after being delivered, Streams **persist messages** until they are explicitly deleted or trimmed. This makes them suitable for systems that require reliability, replayability, acknowledgements, and multiple independent consumers.

Redis Streams combine concepts from:

- Apache Kafka
- RabbitMQ
- Amazon Kinesis
- Event Sourcing
- Message Queues

While they are not intended to replace dedicated streaming platforms in every scenario, Streams provide a lightweight, high-performance solution for many backend applications.

Typical production use cases include:

- Event-driven microservices
- Order processing
- Notification systems
- Audit logging
- IoT data collection
- Real-time analytics
- Background job processing
- Payment event processing
- Inventory updates
- Workflow orchestration

---

# Understanding Redis Streams

A Stream is an ordered sequence of records.

```
payments

↓

+---------------------------------------------+
| ID              | Event                     |
+---------------------------------------------+
| 170001-0        | Payment Created           |
| 170002-0        | Payment Approved          |
| 170003-0        | Payment Completed         |
+---------------------------------------------+
```

Every entry has:

- Unique ID
- One or more field-value pairs

---

# Stream Architecture

```
Producer

↓

Redis Stream

↓

Consumer Group

↓

Consumers
```

Unlike Lists, multiple consumers can read the same stream independently.

---

# Common Stream Commands

| Command | Description |
|----------|-------------|
| XADD | Add message |
| XRANGE | Read message range |
| XREVRANGE | Read reverse range |
| XLEN | Number of messages |
| XDEL | Delete message |
| XTRIM | Trim stream |
| XREAD | Read stream |
| XGROUP CREATE | Create consumer group |
| XREADGROUP | Read as consumer |
| XACK | Acknowledge message |
| XPENDING | View pending messages |
| XCLAIM | Claim pending messages |
| XINFO | Stream information |

---

# Stream IDs

Every Stream message has a unique ID.

Example

```
1700000000123-0
```

Structure

```
Timestamp

↓

Sequence Number
```

Redis automatically generates IDs.

Custom IDs are also supported but rarely used.

---

# XADD

Adds a message to a stream.

Syntax

```redis
XADD stream * field value
```

Example

```redis
XADD orders * order_id 1001 status created
```

Output

```
1700000000123-0
```

Complexity

```
O(log N)
```

---

# Adding Multiple Fields

```redis
XADD payments *

payment_id 100

amount 500

currency USD

status SUCCESS
```

Result

```
1700000005000-0
```

Every event can contain multiple attributes.

---

# XRANGE

Reads messages in ascending order.

Example

```redis
XRANGE orders - +
```

Output

```
ID

↓

Fields

↓

Values
```

Useful for:

- Event replay
- Auditing
- Historical analysis

---

# XREVRANGE

Reads messages in reverse order.

Example

```redis
XREVRANGE orders + -
```

Useful for:

- Latest events
- Recent logs
- Dashboard updates

---

# XLEN

Returns the number of entries.

Example

```redis
XLEN orders
```

Output

```
(integer) 15420
```

Complexity

```
O(1)
```

---

# XDEL

Deletes one or more messages.

Example

```redis
XDEL orders 1700000000123-0
```

Deleted entries leave gaps in the stream IDs.

---

# XTRIM

Limits stream size.

Example

```redis
XTRIM orders MAXLEN 10000
```

Only the newest 10,000 messages remain.

Useful for:

- Memory control
- Log retention
- Event expiration

---

# XREAD

Reads messages.

Example

```redis
XREAD STREAMS orders 0
```

Architecture

```
Application

↓

XREAD

↓

Redis Stream

↓

Messages Returned
```

Useful when consumer groups are unnecessary.

---

# Consumer Groups

Consumer Groups enable multiple workers to process messages collaboratively.

```
Producer

↓

Redis Stream

↓

Consumer Group

↓

Worker A

Worker B

Worker C
```

Each message is processed by only one consumer within the group.

---

# XGROUP CREATE

Creates a consumer group.

Example

```redis
XGROUP CREATE orders workers $
```

Parameters

```
orders

↓

Stream

workers

↓

Consumer Group
```

---

# XREADGROUP

Reads messages as a member of a consumer group.

Example

```redis
XREADGROUP

GROUP workers consumer1

STREAMS

orders

>
```

Redis assigns messages to available consumers.

---

# Message Acknowledgement

Consumers acknowledge successful processing.

```
Consumer

↓

Process Message

↓

XACK

↓

Redis
```

Without acknowledgement, Redis assumes the message is still pending.

---

# XACK

Acknowledges processing.

Example

```redis
XACK

orders

workers

1700000000123-0
```

This removes the message from the Pending Entries List (PEL).

---

# XPENDING

Displays unacknowledged messages.

Example

```redis
XPENDING orders workers
```

Useful for:

- Monitoring failures
- Stuck consumers
- Worker crashes

---

# XCLAIM

Transfers ownership of pending messages.

Example

```redis
XCLAIM

orders

workers

consumer2

60000

1700000000123-0
```

Useful when:

- Consumer crashes
- Worker becomes unavailable
- Automatic recovery

---

# XINFO

Displays stream metadata.

Example

```redis
XINFO STREAM orders
```

Provides information such as:

- Length
- Consumer groups
- First entry
- Last entry

Useful for monitoring.

---

# Event Processing Architecture

```
Payment Service

↓

XADD

↓

Redis Stream

↓

Consumer Group

↓

Payment Worker

↓

Database
```

---

# Notification System

```
Application

↓

Notification Event

↓

Redis Stream

↓

Notification Service

↓

Email

SMS

Push Notification
```

---

# Order Processing

```
Order Created

↓

Redis Stream

↓

Inventory Service

↓

Shipping Service

↓

Billing Service
```

Each service consumes the same stream independently.

---

# IoT Example

```
Sensor

↓

Redis Stream

↓

Analytics

↓

Storage

↓

Alerting
```

Every reading becomes a stream event.

---

# Audit Logging

```
Application

↓

User Login

↓

Redis Stream

↓

Audit Database
```

Streams preserve the event history.

---

# Background Processing

```
Application

↓

XADD

↓

Redis Stream

↓

Worker Pool

↓

XACK
```

Workers acknowledge completed tasks.

---

# Common Production Use Cases

Redis Streams are commonly used for:

- Event sourcing
- Audit logging
- Payment processing
- Order workflows
- Notification queues
- IoT telemetry
- Analytics pipelines
- Background jobs
- Workflow orchestration
- Service integration

---

# Common Mistakes

## Never Trimming Streams

Without trimming:

```
Messages

↓

Millions

↓

Billions

↓

Memory Exhaustion
```

Always use:

```
XTRIM
```

or retention policies.

---

## Forgetting Acknowledgements

Without

```
XACK
```

messages remain pending forever.

---

## Ignoring Pending Messages

Applications should regularly inspect:

```
XPENDING
```

to identify stuck consumers.

---

## Using Streams Instead of Pub/Sub

Streams are persistent.

Pub/Sub is ephemeral.

Choose the correct abstraction.

---

# Best Practices

- Use Consumer Groups for scalable processing.
- Always acknowledge processed messages.
- Trim streams periodically.
- Monitor pending messages.
- Store lightweight payloads.
- Use message IDs for tracing.
- Design idempotent consumers.
- Handle consumer failures gracefully.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| XADD | O(log N) |
| XRANGE | O(log N + M) |
| XREVRANGE | O(log N + M) |
| XLEN | O(1) |
| XDEL | O(1) |
| XTRIM | O(N) |
| XREAD | O(M) |
| XREADGROUP | O(M) |
| XACK | O(1) |
| XPENDING | O(1) |
| XINFO | O(1) |

*M = number of returned messages.*

---

# Streams vs Pub/Sub

| Feature | Streams | Pub/Sub |
|---------|---------|----------|
| Persistent | ✅ | ❌ |
| Replay Messages | ✅ | ❌ |
| Consumer Groups | ✅ | ❌ |
| Acknowledgements | ✅ | ❌ |
| Message History | ✅ | ❌ |
| Fire-and-Forget | ❌ | ✅ |

---

# Production Considerations

For production systems:

- Implement message retention using `XTRIM`.
- Design consumers to be idempotent to safely handle retries.
- Monitor the Pending Entries List (PEL) for stalled messages.
- Use Consumer Groups for horizontal scaling.
- Avoid storing large payloads directly in stream entries; store identifiers and retrieve full data from another source if necessary.
- Implement dead-letter queues or recovery workflows for messages that repeatedly fail processing.
- Monitor stream length, consumer lag, and processing latency.

---

# Summary

Redis Streams provide a durable, scalable, and high-performance messaging mechanism for modern backend systems. Unlike Pub/Sub, Streams retain messages, support replay, acknowledgements, and Consumer Groups, making them ideal for reliable event processing. By combining commands such as `XADD`, `XREADGROUP`, `XACK`, and `XPENDING`, developers can build robust event-driven architectures, workflow engines, and distributed processing systems directly on Redis.

---

# Key Takeaways

- Redis Streams are append-only logs designed for reliable event processing.
- `XADD` adds messages, while `XREAD` and `XREADGROUP` retrieve them.
- Consumer Groups enable multiple workers to process messages collaboratively.
- `XACK` is essential for acknowledging successfully processed messages.
- Use `XPENDING` and `XCLAIM` to manage failed or stalled consumers.
- Trim streams regularly using `XTRIM` to control memory usage.
- Streams are ideal for event-driven architectures, background processing, and audit logging.
- Choose Streams over Pub/Sub when persistence, replayability, or acknowledgements are required.