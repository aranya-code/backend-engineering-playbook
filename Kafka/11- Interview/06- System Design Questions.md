# System Design Questions

## Overview

Kafka is one of the most frequently discussed technologies in System Design interviews for Senior Backend Engineers, Staff Engineers, and Software Architects. Unlike fundamental or API-based questions, System Design interviews focus on **building scalable, reliable, fault-tolerant, and highly available systems**.

Interviewers expect candidates to explain:

- Why Kafka is required
- Where Kafka fits into the architecture
- How to scale Kafka
- How to avoid bottlenecks
- How to guarantee reliability
- Production trade-offs
- Real-world design decisions

This chapter covers some of the most frequently asked Kafka-related System Design interview questions.

---

# Design an Order Processing System

**Question**

> Design an Order Processing System using Kafka.

**Answer**

Example architecture:

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

            Order Service

                   │

                   ▼

          orders.created Topic

      ┌─────────┼──────────┬────────────┐
      ▼         ▼          ▼            ▼

 Inventory   Payment   Notification   Analytics
  Service     Service      Service      Service
```

Advantages:

- Loose coupling
- Independent scaling
- Event replay
- High availability

---

# Design an E-Commerce Platform

**Question**

> Where would Kafka be used in an E-Commerce platform?

**Answer**

```text
Customer

↓

Order Service

↓

Kafka

↓

Inventory

↓

Payment

↓

Shipping

↓

Notification

↓

Recommendation Engine

↓

Analytics
```

Every service consumes only the events it needs.

---

# Design a Notification System

**Question**

> How would you design a scalable notification system?

**Answer**

```text
Application

↓

Kafka

↓

Email Service

↓

SMS Service

↓

Push Notification Service
```

Benefits:

- Independent scaling
- Retry support
- Failure isolation

---

# Design a Payment Processing System

**Question**

> How would Kafka help in payment processing?

**Answer**

```text
Payment Request

↓

Kafka

↓

Fraud Detection

↓

Payment Gateway

↓

Ledger Service

↓

Notification
```

Each service operates independently while maintaining event flow.

---

# Design a Real-Time Analytics Pipeline

**Question**

> Design a real-time analytics platform.

**Answer**

```text
Applications

↓

Kafka

↓

Stream Processing

↓

Analytics Database

↓

Dashboard
```

Kafka buffers high-volume event streams for downstream analytics.

---

# Design a Log Aggregation System

**Question**

> How would you collect logs from thousands of servers?

**Answer**

```text
Servers

↓

Kafka

↓

Log Processor

↓

Search Database

↓

Dashboard
```

Kafka acts as a durable buffer between producers and consumers.

---

# Design an Audit Logging System

**Question**

> Why is Kafka suitable for audit logs?

**Answer**

```text
Microservices

↓

Kafka

↓

Audit Service

↓

Long-Term Storage
```

Advantages:

- Durable storage
- Immutable event history
- Replay capability

---

# Design a Ride Booking Platform

**Question**

> How would Kafka fit into a ride-booking system?

**Answer**

```text
Passenger

↓

Ride Service

↓

Kafka

↓

Driver Matching

↓

Pricing

↓

Payment

↓

Notification

↓

Analytics
```

Every event is published once and consumed by multiple services.

---

# Design an IoT Platform

**Question**

> Millions of IoT devices send telemetry every second. How would you design the ingestion layer?

**Answer**

```text
IoT Devices

↓

Gateway

↓

Kafka

↓

Monitoring

↓

Alerting

↓

Analytics

↓

Data Lake
```

Kafka handles burst traffic efficiently.

---

# Design an Event-Driven Microservices Architecture

**Question**

> How would Kafka be used between microservices?

**Answer**

```text
User Service

↓

Kafka

↓

Profile Service

↓

Recommendation Service

↓

Notification Service

↓

Analytics
```

Microservices communicate asynchronously.

---

# Design for High Availability

**Question**

> How would you make Kafka highly available?

**Answer**

Recommended configuration:

- Minimum 3 brokers
- Replication Factor = 3
- `acks=all`
- `min.insync.replicas=2`
- Multiple Availability Zones
- Monitoring
- Backup strategy

Example:

```text
Broker 1

Broker 2

Broker 3
```

---

# Design for Scalability

**Question**

> Traffic is expected to increase ten times. How would you scale Kafka?

**Answer**

Scale horizontally by:

- Adding brokers
- Increasing partitions
- Increasing consumers
- Optimizing producer batching

Example:

```text
Before

3 Brokers

↓

After

9 Brokers
```

---

# Design for Disaster Recovery

**Question**

> How would you recover from an entire data center failure?

**Answer**

Architecture:

```text
Primary Cluster

↓

MirrorMaker 2

↓

Secondary Cluster
```

Additional measures:

- Cross-region replication
- Automated failover
- Regular backups
- Recovery testing

---

# Design for Exactly Once Processing

**Question**

> How would you ensure financial transactions are processed exactly once?

**Answer**

Use:

- Idempotent Producers
- Transactions
- Manual Offset Commit
- Transaction-aware Consumers

Also ensure business operations are idempotent.

---

# Design for Ordering

**Question**

> Customer events must always remain ordered. How would you design this?

**Answer**

Use:

```text
Customer ID

↓

Partition Key
```

Kafka guarantees ordering within a partition.

---

# Design for Multi-Tenant Applications

**Question**

> How would you support multiple tenants?

**Answer**

Possible strategies:

- Separate topics per tenant
- Shared topics with tenant identifiers
- Separate Consumer Groups
- ACL-based isolation

Choice depends on:

- Scale
- Security
- Operational complexity

---

# Design for Backpressure

**Question**

> Producers are generating messages faster than consumers can process them. What would you do?

**Answer**

Possible solutions:

- Increase consumer instances
- Increase partitions
- Optimize processing
- Batch writes
- Scale downstream systems

Kafka naturally buffers bursts, but persistent lag requires capacity planning.

---

# Design a Dead Letter Queue

**Question**

> How would you handle invalid messages?

**Answer**

```text
Consumer

↓

Invalid Message

↓

Dead Letter Topic

↓

Investigation
```

The consumer continues processing valid records.

---

# Design Monitoring

**Question**

> What metrics would you monitor in a production Kafka cluster?

**Answer**

Monitor:

- Consumer Lag
- Producer Latency
- Request Rate
- Throughput
- Under Replicated Partitions
- ISR
- Disk Usage
- CPU
- Memory
- Network
- JVM Metrics

---

# Design Security

**Question**

> How would you secure a Kafka deployment?

**Answer**

Use:

- SSL/TLS
- SASL Authentication
- ACL Authorization
- Encryption at Rest
- Secrets Management
- Network Isolation
- Audit Logging

---

# Trade-Off Question

**Question**

> Would you always choose Kafka for asynchronous communication?

**Answer**

No.

Kafka is ideal for:

- Event streaming
- Analytics
- Large-scale event pipelines
- Event sourcing

REST or gRPC may be better for:

- Request-response
- Low-latency synchronous communication
- CRUD APIs

Technology should match the problem.

---

# Common Follow-Up Questions

Interviewers often ask:

- Why Kafka instead of RabbitMQ?
- Why Kafka instead of REST?
- How would you monitor the system?
- What happens if a broker crashes?
- How do you scale consumers?
- How do you prevent duplicate processing?
- How would you recover from disaster?
- What are the trade-offs?

---

# Interview Tips

For every System Design question:

1. Clarify assumptions.
2. Define functional requirements.
3. Define non-functional requirements.
4. Draw a high-level architecture.
5. Explain why Kafka is used.
6. Discuss scalability.
7. Discuss fault tolerance.
8. Discuss monitoring.
9. Discuss security.
10. Explain trade-offs.

Interviewers evaluate your reasoning as much as your final design.

---

# Summary

Kafka is a central building block for many large-scale distributed systems because it provides durable event storage, asynchronous communication, scalability, and fault tolerance. In System Design interviews, candidates should demonstrate not only how Kafka works but also where it fits within an architecture, how it scales, how failures are handled, and what trade-offs are involved. Strong answers emphasize real-world production considerations such as monitoring, security, disaster recovery, and operational simplicity.

---

# Key Takeaways

- Kafka is commonly used as the event backbone in distributed architectures.
- System Design interviews focus on architecture and trade-offs rather than API details.
- Kafka enables scalable, fault-tolerant, event-driven systems.
- High availability requires replication, leader election, and proper cluster sizing.
- Ordering is guaranteed within a partition using appropriate message keys.
- Disaster recovery should include cross-region replication and tested recovery procedures.
- Monitoring, security, and capacity planning are essential production concerns.
- Always explain **why** Kafka is the appropriate architectural choice for a given problem.