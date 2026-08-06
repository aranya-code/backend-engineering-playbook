# Consumer Architecture

## Overview

Kafka Consumers are responsible for reading messages from Kafka topics and processing them inside applications.

While producers write data into Kafka, consumers retrieve that data in a scalable, fault-tolerant, and highly parallel manner.

A Kafka consumer does much more than simply reading messages. It:

- Connects to Kafka brokers
- Joins a consumer group
- Reads assigned partitions
- Polls for new records
- Tracks offsets
- Commits processed offsets
- Handles failures and rebalancing

Understanding the consumer architecture is essential before learning concepts such as Poll Loop, Offset Management, Consumer Groups, and Rebalancing.

---

# What is a Kafka Consumer?

A Kafka Consumer is a client application that reads messages from one or more Kafka topics.

Basic architecture:

```text
Producer

↓

Kafka Topic

↓

Consumer
```

Consumers continuously read new events as they arrive.

---

# Producer vs Consumer

| Producer | Consumer |
|----------|----------|
| Writes messages | Reads messages |
| Publishes events | Processes events |
| Chooses partition | Reads assigned partitions |
| Sends records | Polls records |
| Receives acknowledgements | Commits offsets |

Together, producers and consumers enable event-driven communication.

---

# High-Level Consumer Architecture

A Kafka consumer consists of several components working together.

```text
Application
      │
      ▼
Kafka Consumer
      │
      ▼
Consumer Group
      │
      ▼
Group Coordinator
      │
      ▼
Kafka Brokers
      │
      ▼
Topic Partitions
```

Each component has a specific responsibility.

---

# Consumer Components

A Kafka consumer is composed of:

- Consumer Application
- Consumer Client
- Consumer Group
- Group Coordinator
- Kafka Broker
- Topic Partitions
- Offset Storage

Together these components provide scalable and fault-tolerant message consumption.

---

# Consumer Application

This is the business application.

Examples:

- Order Processor
- Notification Service
- Email Service
- Analytics Engine
- Fraud Detection Service

Example:

```text
Order Processor

↓

Kafka Consumer

↓

Orders Topic
```

The application contains the business logic.

---

# Kafka Consumer Client

The Kafka Consumer Client communicates with Kafka brokers.

Responsibilities include:

- Poll messages
- Deserialize records
- Track offsets
- Commit offsets
- Handle rebalancing
- Send heartbeats

Architecture:

```text
Application

↓

Consumer Client

↓

Kafka Cluster
```

---

# Kafka Broker

Consumers communicate directly with Kafka brokers.

```text
Consumer

↓

Broker

↓

Partition Data
```

The broker returns records from assigned partitions.

---

# Topic Partitions

Consumers never read an entire topic directly.

Instead, they read individual partitions.

Example:

```text
Orders Topic

├── Partition 0
├── Partition 1
├── Partition 2
└── Partition 3
```

Each consumer reads one or more assigned partitions.

---

# Consumer Groups

Consumers usually operate as part of a Consumer Group.

Example:

```text
Consumer Group

├── Consumer A
├── Consumer B
└── Consumer C
```

Kafka distributes partitions among consumers in the group.

This enables parallel processing.

---

# Group Coordinator

Every Consumer Group has a Group Coordinator.

Architecture:

```text
Consumer

↓

Group Coordinator

↓

Kafka Cluster
```

Responsibilities:

- Register consumers
- Assign partitions
- Detect failures
- Trigger rebalancing
- Track group membership

Consumers communicate with the coordinator throughout their lifetime.

---

# Partition Assignment

When a consumer joins a group:

```text
Consumer

↓

Group Coordinator

↓

Partition Assignment
```

Example:

```text
Partition 0

↓

Consumer A

-------------------

Partition 1

↓

Consumer B

-------------------

Partition 2

↓

Consumer C
```

Each partition belongs to exactly one consumer within a group.

---

# Message Flow

A simplified message flow:

```text
Producer

↓

Kafka Topic

↓

Partition

↓

Consumer

↓

Business Logic
```

Consumers continuously repeat this process.

---

# Poll-Based Architecture

Kafka uses a **Pull Model**.

Consumers request messages from brokers.

```text
Consumer

↓

Poll()

↓

Broker

↓

Records
```

Kafka does **not** push messages to consumers.

---

# Why Kafka Uses Pull Instead of Push

Push model:

```text
Broker

↓

Consumer
```

Problems:

- Consumer overload
- No flow control
- Buffer exhaustion

Pull model:

```text
Consumer

↓

Broker
```

Advantages:

- Consumer controls speed
- Better backpressure handling
- Predictable resource usage

---

# Consumer Lifecycle

Every consumer follows the same lifecycle.

```text
Start

↓

Connect

↓

Join Group

↓

Receive Partition Assignment

↓

Poll Records

↓

Process Records

↓

Commit Offsets

↓

Repeat

↓

Shutdown
```

Most of Kafka's consumer behavior revolves around this lifecycle.

---

# Offset Tracking

Consumers track how much data has been processed.

Example:

```text
Partition

0

1

2

3

4

5

6

7

Current Offset

↓

5
```

The next poll begins from Offset 6.

Offsets allow consumers to resume after failures.

---

# Heartbeats

Consumers periodically send heartbeat messages.

```text
Consumer

↓

Heartbeat

↓

Group Coordinator
```

Heartbeats tell Kafka:

```text
Consumer

↓

Alive
```

If heartbeats stop:

```text
Consumer

↓

Dead

↓

Rebalance
```

---

# Rebalancing

Suppose a consumer crashes.

Before:

```text
Consumer A

Partition 0

Consumer B

Partition 1
```

Consumer B fails.

After:

```text
Consumer A

Partition 0

Partition 1
```

Kafka automatically redistributes partitions.

---

# Consumer Parallelism

Suppose:

```text
Topic

4 Partitions
```

Consumer Group:

```text
Consumer A

Consumer B

Consumer C

Consumer D
```

Result:

```text
P0 → A

P1 → B

P2 → C

P3 → D
```

All four partitions are processed simultaneously.

---

# Consumer Architecture Diagram

```text
                  Kafka Cluster
      ┌──────────────────────────────┐
      │                              │
      │        Orders Topic          │
      │                              │
      │ P0  P1  P2  P3               │
      └──────────────────────────────┘
          │   │   │   │
          ▼   ▼   ▼   ▼
      ┌──────────────────────┐
      │   Consumer Group     │
      ├──────────────────────┤
      │ Consumer A → P0      │
      │ Consumer B → P1      │
      │ Consumer C → P2      │
      │ Consumer D → P3      │
      └──────────────────────┘
                 │
                 ▼
         Business Applications
```

---

# Real-World Example

An online shopping platform publishes order events.

```text
Orders Topic

↓

Consumer Group

↓

Inventory Service

↓

Payment Service

↓

Shipping Service
```

Each service processes events independently while maintaining scalability.

---

# Advantages of Consumer Architecture

- Horizontal scalability
- Fault tolerance
- Automatic recovery
- Parallel processing
- Independent consumers
- Efficient load balancing
- Flexible offset management
- High throughput

---

# Best Practices

- Always use Consumer Groups for scalable applications.
- Keep consumer processing fast to avoid poll timeouts.
- Monitor consumer lag.
- Handle rebalancing correctly.
- Commit offsets only after successful processing.
- Use meaningful `group.id` values.
- Design applications to tolerate duplicate message processing.

---

# Common Mistakes

- Assuming Kafka pushes messages to consumers.
- Believing multiple consumers in the same group can read the same partition simultaneously.
- Ignoring offset management.
- Performing long-running work inside the poll loop.
- Not understanding how rebalancing affects message processing.

---

# Summary

Kafka Consumers are responsible for retrieving and processing messages stored in Kafka topics. They operate using a pull-based architecture, where consumers poll brokers for new records, track offsets, participate in consumer groups, and process assigned partitions. Components such as the Group Coordinator, offset management, heartbeats, and rebalancing work together to provide scalability, fault tolerance, and reliable message consumption. Understanding the consumer architecture forms the foundation for learning advanced concepts such as poll loops, offset management, rebalancing, and delivery semantics.

---

# Key Takeaways

- Kafka consumers read messages from topic partitions.
- Consumers use a pull-based model by polling brokers for new records.
- Consumer Groups enable scalable and parallel message processing.
- The Group Coordinator manages consumer membership and partition assignment.
- Consumers track progress using offsets.
- Heartbeats keep consumers active within a group.
- Rebalancing redistributes partitions when group membership changes.
- Consumer architecture provides the scalability and fault tolerance required for modern event-driven systems.