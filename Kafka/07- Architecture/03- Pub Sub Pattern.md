# Pub Sub Pattern

## Overview

The **Publish-Subscribe (Pub/Sub)** pattern is one of the most widely used messaging patterns in distributed systems. It allows applications to communicate **indirectly** through a messaging system instead of calling each other directly.

In Apache Kafka, producers **publish** messages to topics, while consumers **subscribe** to those topics to receive messages. The producer does not know who consumes the data, and the consumers do not know who produced it. Kafka acts as the intermediary that connects both sides.

This loose coupling enables scalable, resilient, and highly maintainable event-driven systems.

---

# What is the Publish-Subscribe Pattern?

The Publish-Subscribe (Pub/Sub) pattern is a messaging architecture where:

- Publishers send messages
- Subscribers receive messages
- A broker delivers messages between them

Unlike direct communication, publishers and subscribers never communicate with each other directly.

---

# Basic Architecture

```text
Publisher

↓

Message Broker

↓

Subscriber
```

Kafka acts as the **Message Broker**.

---

# Kafka Pub/Sub Architecture

```text
                Producer

                    │

                    ▼

              Kafka Topic

        ┌───────────┼───────────┐

        ▼           ▼           ▼

Inventory      Shipping     Analytics

Consumer        Consumer      Consumer
```

A single published message can be consumed by multiple independent applications.

---

# Publisher

A Publisher (Producer) creates events.

Example:

```text
Order Service

↓

Order Created Event
```

The producer only knows:

- Topic name
- Kafka cluster

It has no knowledge of consumers.

---

# Subscriber

Subscribers (Consumers) listen for events.

Example:

```text
Orders Topic

↓

Inventory Service

↓

Notification Service

↓

Analytics Service
```

Each subscriber performs its own business logic.

---

# Broker

Kafka sits between producers and consumers.

```text
Producer

↓

Kafka

↓

Consumers
```

Responsibilities:

- Store messages
- Deliver messages
- Maintain ordering
- Handle replication
- Manage offsets

---

# Message Flow

```text
Producer

↓

Publish Event

↓

Kafka Topic

↓

Consumer Groups

↓

Consumers
```

The producer's job ends once Kafka acknowledges the message.

---

# Example: E-Commerce

Customer places an order.

```text
Customer

↓

Order Service

↓

Order Created

↓

Kafka
```

Subscribers:

```text
Inventory

↓

Reserve Stock

----------------

Shipping

↓

Prepare Shipment

----------------

Notification

↓

Send Email

----------------

Analytics

↓

Update Dashboard
```

Every service works independently.

---

# One Publisher, Multiple Subscribers

One producer can notify many consumers.

```text
Order Service

↓

Kafka

├── Inventory

├── Shipping

├── Analytics

├── Billing

└── Email
```

This is one of Kafka's greatest strengths.

---

# Multiple Publishers

Kafka also supports multiple publishers.

```text
Order Service

↓

Payment Service

↓

Customer Service

↓

Kafka
```

Each service publishes to one or more topics.

---

# Multiple Topics

Applications can publish to multiple topics.

```text
Order Service

↓

orders

↓

payments

↓

notifications
```

Each topic represents a different event stream.

---

# Consumer Groups

Subscribers usually belong to Consumer Groups.

Example:

```text
Orders Topic

↓

Inventory Group

↓

Shipping Group

↓

Analytics Group
```

Each group receives every message independently.

---

# Within a Consumer Group

Suppose:

```text
Orders Topic

↓

4 Partitions
```

Consumer Group:

```text
Consumer A

↓

Partition 0

↓

Partition 2

----------------

Consumer B

↓

Partition 1

↓

Partition 3
```

Messages are distributed among consumers within the same group.

---

# Different Consumer Groups

Multiple groups receive the same event.

```text
Orders Topic

↓

Inventory Group

↓

Shipping Group

↓

Analytics Group
```

Kafka maintains separate offsets for every Consumer Group.

---

# Loose Coupling

Traditional architecture:

```text
Order Service

↓

Inventory Service

↓

Notification Service
```

Every service depends on another.

Kafka:

```text
Order Service

↓

Kafka

↓

Inventory

↓

Shipping

↓

Analytics
```

Services only depend on Kafka.

---

# Asynchronous Communication

Request-response:

```text
Send Request

↓

Wait

↓

Response
```

Publish-Subscribe:

```text
Publish Event

↓

Continue Processing
```

Consumers process the event independently.

---

# Event Replay

Suppose a new consumer is added.

```text
Recommendation Engine

↓

Replay Events

↓

Build Recommendations
```

Kafka allows replay as long as events remain within the retention period.

---

# Failure Isolation

Suppose:

```text
Analytics Service

↓

Offline
```

Kafka continues storing events.

When Analytics restarts:

```text
Analytics

↓

Replay Messages

↓

Continue Processing
```

Other consumers are unaffected.

---

# Pub/Sub vs Point-to-Point

## Point-to-Point

```text
Producer

↓

Queue

↓

One Consumer
```

Each message is consumed once.

---

## Publish-Subscribe

```text
Producer

↓

Kafka Topic

↓

Consumer Group A

↓

Consumer Group B

↓

Consumer Group C
```

Every Consumer Group receives the event.

---

# Real-World Example

Online shopping system.

```text
Order Created

↓

Kafka

├── Inventory Service
├── Shipping Service
├── Fraud Detection
├── Recommendation Engine
├── Analytics
└── Notification Service
```

Adding another consumer requires no changes to the producer.

---

# Benefits

The Pub/Sub pattern provides:

- Loose coupling
- Independent services
- Easy scalability
- Better fault tolerance
- Event replay
- Flexible integrations
- Independent deployments
- Real-time communication

---

# Challenges

The pattern also introduces challenges.

Examples:

- Duplicate events
- Event ordering
- Schema evolution
- Consumer lag
- Monitoring
- Eventual consistency
- Distributed debugging

These challenges are addressed through Kafka features such as Consumer Groups, offsets, idempotent consumers, and Schema Registry.

---

# Pub/Sub Architecture

```text
Business Event
        │
        ▼
Producer
        │
        ▼
Kafka Topic
        │
 ┌──────┼──────┬──────┐
 ▼      ▼      ▼      ▼
Inventory Shipping Analytics Notifications
```

Each consumer operates independently.

---

# Best Practices

- Publish business events instead of implementation details.
- Keep publishers independent of subscribers.
- Design topics around business domains.
- Use Consumer Groups for horizontal scalability.
- Make consumers idempotent.
- Monitor consumer lag.
- Use Schema Registry for message evolution.
- Document event contracts clearly.

---

# Common Mistakes

- Assuming producers know who the consumers are.
- Treating Kafka as a direct messaging system.
- Mixing unrelated events into one topic.
- Ignoring Consumer Groups.
- Designing tightly coupled event flows.
- Forgetting about eventual consistency.
- Assuming one consumer failure affects all others.

---

# Summary

The Publish-Subscribe pattern is the foundation of Kafka's communication model. Producers publish events to Kafka topics without knowing who will consume them, while multiple Consumer Groups independently subscribe and process those events. This loose coupling enables scalable, fault-tolerant, and highly extensible systems where services evolve independently without requiring changes to publishers. Kafka enhances the traditional Pub/Sub pattern with durable storage, event replay, partitioning, and Consumer Groups, making it one of the most powerful messaging platforms for modern distributed systems.

---

# Key Takeaways

- Publish-Subscribe decouples producers from consumers.
- Kafka topics act as communication channels between publishers and subscribers.
- One producer can publish events to many Consumer Groups.
- Each Consumer Group receives every event independently.
- Kafka provides durable storage and replay capabilities beyond traditional Pub/Sub systems.
- The pattern enables scalable, event-driven architectures.
- Loose coupling improves maintainability and fault tolerance.
- Pub/Sub is a core architectural pattern for building modern distributed systems.