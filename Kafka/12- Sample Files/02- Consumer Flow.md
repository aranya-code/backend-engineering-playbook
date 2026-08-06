# Consumer Flow

## Overview

A Kafka Consumer is responsible for reading messages from Kafka topics and processing them. Unlike traditional messaging systems that push messages to consumers, Kafka uses a **pull-based model**, where consumers actively request new data from brokers.

A consumer does much more than simply reading records. It joins a Consumer Group, receives partition assignments, continuously polls for new messages, processes them, commits offsets, and repeats the cycle.

Understanding the complete consumer flow is essential for building reliable Kafka applications and troubleshooting production issues.

---

# Consumer Flow

The complete consumer flow is:

```text
Application

↓

Consumer Starts

↓

Join Consumer Group

↓

Partition Assignment

↓

Poll Records

↓

Deserialize

↓

Process Message

↓

Commit Offset

↓

Poll Again
```

---

# Step 1: Consumer Starts

The application creates a Kafka Consumer.

Example:

```java
KafkaConsumer<String, String>
```

The consumer knows:

- Bootstrap servers
- Consumer Group ID
- Topics
- Deserializers

Example:

```text
Inventory Service

↓

Kafka Consumer
```

---

# Step 2: Join Consumer Group

The consumer joins a Consumer Group.

```text
Consumer

↓

Consumer Group
```

Example:

```text
inventory-group
```

Kafka registers the consumer with the Group Coordinator.

---

# Step 3: Group Coordinator

The coordinator manages:

- Consumer membership
- Heartbeats
- Rebalancing
- Partition assignment

Workflow:

```text
Consumer

↓

Group Coordinator
```

Every Consumer Group has exactly one coordinator.

---

# Step 4: Partition Assignment

Kafka assigns partitions.

Example:

```text
Orders Topic

↓

Partition 0

↓

Consumer A

-----------------

Partition 1

↓

Consumer B
```

Each partition belongs to only one consumer within the group.

---

# Step 5: Poll Records

Consumers request messages.

```java
consumer.poll(...)
```

Workflow:

```text
Consumer

↓

Broker

↓

Records Returned
```

Kafka never pushes messages.

---

# Step 6: Fetch From Broker

The broker reads messages from the partition log.

```text
Partition Log

↓

Read Records

↓

Consumer
```

The broker sends a batch of records.

---

# Step 7: Deserialization

Kafka stores bytes.

The consumer converts them back into objects.

```text
Byte Array

↓

Deserializer

↓

Application Object
```

Common deserializers:

- String
- JSON
- Avro
- Protobuf

---

# Step 8: Process Messages

Business logic executes.

Example:

```text
Receive Order

↓

Reserve Inventory

↓

Update Database

↓

Send Email
```

Processing time directly affects Consumer Lag.

---

# Step 9: Commit Offset

After successful processing:

```text
Message Processed

↓

Commit Offset
```

Kafka records consumer progress.

---

# Auto Commit

If enabled:

```properties
enable.auto.commit=true
```

Kafka periodically commits offsets automatically.

```text
Poll

↓

Process

↓

Automatic Commit
```

Simple but less reliable.

---

# Manual Commit

With manual commits:

```text
Poll

↓

Process Successfully

↓

Commit Offset
```

Preferred for production systems.

---

# Step 10: Poll Again

The consumer repeats the cycle.

```text
Poll

↓

Process

↓

Commit

↓

Poll Again
```

Consumers continuously process new events.

---

# Complete Consumer Flow Diagram

```text
Application
      │
      ▼
Consumer Starts
      │
      ▼
Join Consumer Group
      │
      ▼
Partition Assignment
      │
      ▼
Poll Records
      │
      ▼
Deserialize
      │
      ▼
Business Logic
      │
      ▼
Commit Offset
      │
      ▼
Poll Again
```

---

# Example

Suppose a new order arrives.

```text
orders.created
```

Consumer flow:

```text
Consumer Starts

↓

Join Group

↓

Assigned Partition

↓

Poll Message

↓

Deserialize JSON

↓

Update Inventory

↓

Commit Offset

↓

Wait For Next Poll
```

---

# What Happens if the Consumer Crashes?

Suppose:

```text
Poll

↓

Process

↓

Crash
```

Kafka detects:

```text
Heartbeat Timeout

↓

Rebalance

↓

Partition Assigned

↓

Another Consumer Continues
```

If the offset wasn't committed:

```text
Message Processed Again
```

Duplicates may occur.

---

# What Happens During Rebalancing?

Suppose a new consumer joins.

```text
Consumer A

Consumer B

↓

Consumer C Joins
```

Kafka performs:

```text
Pause Consumption

↓

Reassign Partitions

↓

Resume Consumption
```

This ensures balanced workload distribution.

---

# What Happens if Processing Is Slow?

Example:

```text
Poll

↓

Database

↓

REST API

↓

Machine Learning

↓

Commit
```

Processing exceeds:

```properties
max.poll.interval.ms
```

Kafka assumes the consumer has failed.

Result:

```text
Consumer Removed

↓

Rebalance
```

---

# Consumer Flow with Multiple Consumers

```text
Orders Topic

       │

       ▼

Consumer Group

 ┌──────────────┐

 ▼              ▼

Consumer A   Consumer B

 │              │

 ▼              ▼

Partition 0   Partition 1
```

Parallel processing improves throughput.

---

# Consumer Flow During Failure

```text
Consumer

↓

Broker Failure

↓

Leader Election

↓

Retry Poll

↓

Continue Processing
```

Consumers automatically reconnect after temporary failures.

---

# Consumer Configuration Affecting Flow

Important settings:

```properties
enable.auto.commit
```

Controls automatic offset commits.

---

```properties
auto.offset.reset
```

Determines starting offset.

---

```properties
max.poll.interval.ms
```

Maximum processing interval.

---

```properties
session.timeout.ms
```

Heartbeat timeout.

---

```properties
max.poll.records
```

Maximum records returned per poll.

---

# Real-World Example

Food delivery application:

```text
Restaurant Accepts Order

↓

orders.accepted Topic

↓

Inventory Consumer

↓

Reserve Ingredients

↓

Commit Offset

↓

Wait For Next Order
```

Other consumers:

```text
Notification

Analytics

Delivery

Billing
```

Each Consumer Group processes the same event independently.

---

# Best Practices

- Commit offsets only after successful processing.
- Keep processing fast.
- Monitor Consumer Lag.
- Handle duplicate processing safely.
- Use Manual Commit for critical workloads.
- Configure heartbeat and polling correctly.
- Batch expensive operations.
- Monitor Consumer Groups continuously.
- Handle deserialization failures gracefully.
- Design consumers to be idempotent.

---

# Common Mistakes

- Committing offsets before processing.
- Ignoring Consumer Lag.
- Blocking the poll loop with long-running tasks.
- Using Auto Commit for business-critical workloads.
- Ignoring heartbeat timeouts.
- Allowing frequent rebalancing.
- Crashing consumers on malformed messages.
- Scaling consumers without increasing partitions.

---

# Summary

The Kafka Consumer Flow begins when a consumer joins a Consumer Group and receives partition assignments. It continuously polls brokers for new records, deserializes messages, executes business logic, commits offsets after successful processing, and repeats the cycle. Understanding each stage of this flow is essential for building reliable, fault-tolerant, and scalable event-driven applications that can recover gracefully from failures while maintaining efficient message processing.

---

# Key Takeaways

- Consumers actively poll Kafka for new messages.
- Consumer Groups enable scalable parallel processing.
- Partition assignment determines which consumer processes each partition.
- Messages are deserialized before business logic executes.
- Offsets track consumer progress.
- Manual offset commits improve reliability.
- Consumer Lag is a key indicator of processing health.
- Understanding the consumer flow is fundamental to designing robust Kafka consumers.