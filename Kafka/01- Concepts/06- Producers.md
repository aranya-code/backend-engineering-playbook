# Producers

## Overview

A **Producer** is a client application that publishes messages (events) to Apache Kafka. Every piece of data entering Kafka is sent by a producer.

Whether it's an order being placed, a payment being processed, a user signing in, or an IoT sensor sending data, the producer is responsible for delivering these events to the appropriate Kafka topic.

The producer is the starting point of every Kafka data pipeline.

---

# What is a Producer?

A producer is any application capable of writing data to Kafka.

For example:

- Order Service
- Payment Service
- Mobile Application
- Backend API
- Web Application
- IoT Device
- Log Aggregator
- Monitoring System

The producer's responsibility is simple:

1. Create an event.
2. Connect to Kafka.
3. Send the event to a topic.

---

# Producer Architecture

A high-level producer architecture looks like this.

```text
Application

     │

     ▼

Kafka Producer

     │

     ▼

Kafka Cluster

     │

     ▼

Topic
```

The producer never communicates directly with consumers.

Its only responsibility is writing events into Kafka.

---

# Producer Workflow

The lifecycle of a producer follows these steps.

```text
Create Message

      │

      ▼

Serialize Message

      │

      ▼

Choose Topic

      │

      ▼

Choose Partition

      │

      ▼

Send to Broker

      │

      ▼

Receive Acknowledgement
```

Once Kafka acknowledges the write, the producer considers the operation complete.

---

# Real-World Example

Imagine an online shopping application.

A customer places an order.

```text
Customer

     │

     ▼

Order Service

     │

     ▼

Kafka Producer

     │

     ▼

orders Topic
```

The producer sends an event similar to:

```json
{
    "order_id": 1054,
    "customer_id": 201,
    "amount": 1500
}
```

Kafka stores this event.

Multiple services can consume it independently.

---

# Producer Components

A Kafka producer consists of several internal components.

```text
Application

      │

      ▼

Serializer

      │

      ▼

Partitioner

      │

      ▼

Buffer

      │

      ▼

Kafka Broker
```

Each component performs a specific task before the message reaches Kafka.

---

# Creating a Message

Every producer begins by creating a message.

Example:

```text
Order Created
```

or

```json
{
    "order_id": 101,
    "status": "CREATED"
}
```

The producer prepares this data before sending it to Kafka.

---

# Serialization

Kafka stores data as bytes.

Before sending data, the producer converts objects into bytes.

This process is called **serialization**.

```text
Python Object

↓

Serializer

↓

Byte Array

↓

Kafka
```

Common serializers include:

- String Serializer
- JSON Serializer
- Avro Serializer
- Protobuf Serializer

Serialization will be discussed in detail later.

---

# Choosing a Topic

Every producer must specify a topic.

Example:

```text
Producer

↓

orders
```

or

```text
Producer

↓

payments
```

Kafka stores the message inside the selected topic.

---

# Choosing a Partition

Kafka determines the destination partition.

Three approaches are commonly used.

## 1. Message Key

If a key is supplied:

```text
Customer ID

↓

Hash Function

↓

Partition
```

The same key always maps to the same partition.

This preserves message ordering for that key.

---

## 2. Round Robin

If no key is provided:

```text
Message 1

↓

Partition 0

---------------

Message 2

↓

Partition 1

---------------

Message 3

↓

Partition 2
```

Kafka balances traffic evenly.

---

## 3. Custom Partitioner

Applications can implement custom routing logic.

Example:

```text
Premium Orders

↓

Partition 0

Regular Orders

↓

Partition 1
```

This is useful when business rules determine partition placement.

---

# Sending Messages

After partition selection, the producer sends the message to the leader broker responsible for that partition.

```text
Producer

      │

      ▼

Leader Broker

      │

      ▼

Partition
```

Followers receive replicated copies after the leader accepts the message.

---

# Producer Acknowledgements

Kafka informs the producer whether the write succeeded.

This response is called an **acknowledgement (ACK)**.

There are three acknowledgement levels.

---

## acks = 0

The producer does not wait for any acknowledgement.

```text
Producer

↓

Send Message

↓

Continue
```

Advantages:

- Fastest

Disadvantages:

- Possible data loss

---

## acks = 1

The producer waits for the leader broker.

```text
Producer

↓

Leader

↓

ACK
```

Advantages:

- Good performance
- Reasonable reliability

Disadvantages:

- Leader failure before replication may cause data loss.

---

## acks = all

The producer waits until all in-sync replicas acknowledge the message.

```text
Producer

↓

Leader

↓

Followers

↓

ACK
```

Advantages:

- Highest reliability

Disadvantages:

- Slightly higher latency

This is the recommended setting for production systems.

---

# Producer Retries

Sometimes a broker may be temporarily unavailable.

Instead of immediately failing, producers retry.

```text
Send

↓

Failure

↓

Retry

↓

Success
```

Retries improve reliability during transient failures.

---

# Batching

Rather than sending every message individually, producers group multiple messages into a batch.

Without batching:

```text
Message

↓

Network

Message

↓

Network

Message

↓

Network
```

With batching:

```text
Message

Message

Message

↓

Single Network Request
```

Benefits:

- Higher throughput
- Lower network overhead
- Better performance

---

# Compression

Kafka producers can compress batches before transmission.

Example algorithms include:

- gzip
- snappy
- lz4
- zstd

Benefits:

- Reduced network traffic
- Lower storage usage
- Improved throughput

Compression is configured on the producer.

---

# Idempotent Producer

An idempotent producer prevents duplicate messages caused by retries.

Without idempotency:

```text
Retry

↓

Duplicate Message
```

With idempotency:

```text
Retry

↓

Single Stored Message
```

This feature is highly recommended for production workloads.

---

# Producer Failures

Possible failures include:

- Broker unavailable
- Network interruption
- Timeout
- Serialization failure
- Authentication error

The producer should handle these failures gracefully using retries, logging, and appropriate error handling.

---

# Producer Configuration

Common configuration options include:

| Configuration | Purpose |
|--------------|---------|
| bootstrap.servers | Kafka broker addresses |
| acks | Acknowledgement level |
| retries | Number of retry attempts |
| linger.ms | Batch wait time |
| batch.size | Maximum batch size |
| compression.type | Compression algorithm |
| enable.idempotence | Prevent duplicate writes |
| client.id | Producer identifier |

Each option influences performance and reliability.

---

# Best Practices

- Use meaningful topic names.
- Use message keys when ordering is important.
- Prefer `acks=all` in production.
- Enable retries.
- Enable idempotent producers.
- Batch messages for better throughput.
- Use compression for high-volume workloads.
- Handle producer exceptions properly.
- Monitor producer metrics.

---

# Common Mistakes

- Sending every message individually.
- Ignoring retries.
- Using `acks=0` in production.
- Not providing keys when ordering matters.
- Disabling idempotency for critical systems.
- Sending extremely large messages.
- Ignoring serialization errors.

---

# Summary

A Kafka producer is responsible for publishing events to Kafka topics. Before a message reaches Kafka, the producer serializes the data, selects a partition, sends the message to the leader broker, and waits for an acknowledgement based on its configuration. Features such as retries, batching, compression, acknowledgements, and idempotent writes allow producers to achieve both high performance and strong reliability in production environments.

---

# Key Takeaways

- Producers publish messages to Kafka topics.
- Every Kafka data pipeline begins with a producer.
- Messages are serialized before transmission.
- Kafka selects a partition based on keys or partitioning strategy.
- Producers send messages to the leader broker.
- Acknowledgements determine write reliability.
- Retries and idempotent producers improve fault tolerance.
- Batching and compression significantly improve throughput.
- Proper producer configuration is essential for production systems.
- Producers are the entry point for event-driven architectures.