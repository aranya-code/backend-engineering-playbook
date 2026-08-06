# Event Driven Architecture

## Overview

Traditional applications often rely on direct communication between services using synchronous APIs. While this approach is simple, it creates tight coupling, reduces scalability, and makes systems more difficult to maintain as they grow.

**Event-Driven Architecture (EDA)** addresses these challenges by allowing applications to communicate through **events** rather than direct requests. Instead of one service calling another, a service publishes an event describing something that has happened. Other services subscribe to those events and react independently.

Apache Kafka is one of the most popular platforms for implementing Event-Driven Architecture because of its scalability, durability, and support for real-time event streaming.

---

# What is an Event?

An event is a record that describes something that has already happened in the system.

Examples:

```text
Order Created

Payment Completed

Customer Registered

Product Added

Invoice Generated

Shipment Delivered
```

An event represents a fact, not a command.

---

# What is Event-Driven Architecture?

Event-Driven Architecture is a software architecture where applications communicate by producing and consuming events.

Instead of:

```text
Service A

↓

Calls

↓

Service B
```

The communication becomes:

```text
Service A

↓

Publishes Event

↓

Kafka

↓

Service B
```

Neither service needs to know about the other.

---

# Traditional Request-Response Architecture

Example:

```text
Customer

↓

API Gateway

↓

Order Service

↓

Inventory Service

↓

Payment Service

↓

Notification Service
```

Every service depends on another service.

Problems:

- Tight coupling
- Cascading failures
- High latency
- Difficult scaling

---

# Event-Driven Architecture

```text
Order Service

↓

Order Created Event

↓

Kafka

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service

↓

Notification Service
```

Each consumer processes the event independently.

---

# Core Components

An Event-Driven Architecture consists of:

- Event Producer
- Event Broker
- Event Consumer
- Event

Kafka acts as the Event Broker.

---

# Producer

A producer generates events.

Example:

```text
Order Service

↓

Order Created
```

The producer publishes the event to Kafka.

---

# Event Broker

Kafka receives events.

```text
Producer

↓

Kafka

↓

Topic

↓

Partition
```

Kafka stores the events until consumers process them.

---

# Consumer

Consumers subscribe to topics.

Example:

```text
Orders Topic

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service
```

Every consumer performs different business logic.

---

# Event Flow

```text
Business Action

↓

Producer

↓

Kafka Topic

↓

Consumer Group

↓

Business Processing
```

This is the fundamental workflow of an event-driven system.

---

# Example: Online Shopping

Customer places an order.

```text
Customer

↓

Order Service

↓

Order Created Event

↓

Kafka
```

Consumers:

```text
Inventory Service

↓

Reserve Stock

----------------

Payment Service

↓

Charge Customer

----------------

Email Service

↓

Send Confirmation

----------------

Analytics Service

↓

Update Dashboard
```

No consumer communicates directly with another.

---

# Loose Coupling

Traditional:

```text
Order Service

↓

Inventory Service

↓

Notification Service
```

Dependencies exist between services.

Event-driven:

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

↓

Notifications
```

Services only depend on Kafka.

---

# Independent Scaling

Suppose analytics becomes busy.

Traditional:

```text
Entire System

↓

Slow
```

Event-driven:

```text
Analytics

↓

Scale Independently
```

Other services continue unaffected.

---

# Asynchronous Communication

Request-response:

```text
Request

↓

Wait

↓

Response
```

Event-driven:

```text
Publish Event

↓

Continue Processing
```

The producer does not wait for consumers.

---

# Multiple Consumers

One event can be processed by many applications.

```text
Order Created

↓

Inventory

↓

Shipping

↓

Fraud Detection

↓

Billing

↓

Analytics

↓

Email
```

Kafka delivers the same event to multiple Consumer Groups.

---

# Event Persistence

Unlike traditional message brokers, Kafka stores events.

```text
Producer

↓

Kafka Log

↓

Consumers

↓

Replay Possible
```

Applications can replay historical events.

---

# Event Replay

Suppose a new service is added.

```text
Recommendation Engine

↓

Replay Events

↓

Build Recommendations
```

Kafka enables rebuilding application state from historical events.

---

# Failure Isolation

Suppose:

```text
Notification Service

↓

Offline
```

Kafka continues storing events.

```text
Notification Service

↓

Restart

↓

Replay Messages
```

Other services continue operating normally.

---

# Real-World Architecture

```text
                Customer
                    │
                    ▼
             Order Service
                    │
                    ▼
          Order Created Event
                    │
                    ▼
                 Kafka
     ┌────────┬────────┬────────┬────────┐
     ▼        ▼        ▼        ▼
Inventory Shipping Analytics Email
```

Every service processes the same event independently.

---

# Advantages

Event-Driven Architecture provides:

- Loose coupling
- Horizontal scalability
- High availability
- Better fault tolerance
- Independent deployments
- Event replay
- Real-time processing
- Easier integration

---

# Challenges

EDA also introduces complexity.

Common challenges include:

- Event ordering
- Duplicate events
- Event versioning
- Schema evolution
- Eventual consistency
- Distributed debugging
- Monitoring asynchronous workflows

These challenges require careful architectural design.

---

# Eventual Consistency

Unlike synchronous systems:

```text
Update Database

↓

Immediate Result
```

EDA becomes:

```text
Publish Event

↓

Consumers Process

↓

Eventually Consistent
```

Different services may update at different times.

---

# Typical Use Cases

Event-Driven Architecture is widely used in:

- E-commerce
- Banking
- Payment Systems
- IoT Platforms
- Fraud Detection
- Logistics
- Recommendation Engines
- Real-Time Analytics
- Microservices
- Financial Trading

---

# Architecture Diagram

```text
Business Action
        │
        ▼
Application
        │
        ▼
Producer
        │
        ▼
Kafka Topic
        │
        ▼
Consumer Group 1
        │
        ▼
Inventory Service

Consumer Group 2
        │
        ▼
Shipping Service

Consumer Group 3
        │
        ▼
Analytics Service

Consumer Group 4
        │
        ▼
Notification Service
```

---

# Best Practices

- Publish business events instead of technical events.
- Design immutable events.
- Use meaningful topic names.
- Keep producers and consumers loosely coupled.
- Make consumers idempotent.
- Version event schemas carefully.
- Monitor consumer lag and processing failures.
- Use Schema Registry for schema evolution.

---

# Common Mistakes

- Treating Kafka like a traditional message queue.
- Publishing commands instead of events.
- Creating tightly coupled consumers.
- Ignoring schema evolution.
- Assuming synchronous behavior.
- Forgetting about eventual consistency.
- Mixing unrelated business events in one topic.

---

# Summary

Event-Driven Architecture enables applications to communicate by publishing and consuming events rather than making direct synchronous calls. Kafka acts as the central event broker, allowing multiple independent consumers to process the same events while providing scalability, fault tolerance, and durable event storage. By embracing loose coupling and asynchronous communication, organizations can build resilient, highly scalable systems capable of evolving independently over time.

---

# Key Takeaways

- Event-Driven Architecture is based on producers publishing events and consumers reacting to them.
- Kafka is a popular platform for implementing EDA.
- Services communicate indirectly through events rather than direct API calls.
- Multiple Consumer Groups can independently process the same event.
- Kafka stores events, enabling replay and recovery.
- Event-driven systems are loosely coupled and highly scalable.
- Eventual consistency is a fundamental characteristic of EDA.
- Understanding Event-Driven Architecture is essential for designing modern distributed systems.