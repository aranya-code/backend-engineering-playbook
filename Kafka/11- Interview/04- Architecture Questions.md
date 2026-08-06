# Architecture Questions

## Overview

Kafka is a core component of modern event-driven architectures and distributed systems. As a result, architecture-related Kafka questions are extremely common in senior backend, system design, and software architect interviews.

Interviewers are less interested in API syntax and more interested in understanding:

- Why Kafka is used
- When Kafka should be used
- System design trade-offs
- Scalability
- Reliability
- High Availability
- Event-driven architecture
- Real-world production design

This chapter covers the most frequently asked Kafka architecture interview questions with concise, production-focused answers.

---

# Why Do Companies Use Kafka?

**Question**

> Why do companies use Kafka?

**Answer**

Companies use Kafka because it provides:

- High throughput
- Horizontal scalability
- Fault tolerance
- Durable storage
- Event replay
- Loose coupling between services

Kafka enables reliable communication between distributed systems.

---

# Where Does Kafka Fit in an Architecture?

**Question**

> Where is Kafka typically used?

**Answer**

Kafka usually sits between producers and consumers.

```text
Microservice

↓

Kafka

↓

Microservice
```

It decouples services and enables asynchronous communication.

---

# What Problems Does Kafka Solve?

**Question**

> What problems does Kafka solve?

**Answer**

Kafka solves:

- Tight coupling
- Synchronous communication
- Traffic spikes
- Event distribution
- Scalability
- Reliable message delivery
- Event replay

---

# Explain an Event-Driven Architecture

**Question**

> What is an Event-Driven Architecture?

**Answer**

Applications communicate by publishing events.

Example:

```text
Order Service

↓

Order Created

↓

Kafka

↓

Inventory

↓

Payment

↓

Notification

↓

Analytics
```

Services are independent.

---

# Why Is Kafka Better Than Direct REST Calls?

**Question**

> Why use Kafka instead of REST?

**Answer**

REST:

```text
Service A

↓

Service B
```

Both services must be available.

Kafka:

```text
Service A

↓

Kafka

↓

Service B
```

Benefits:

- Asynchronous
- Better scalability
- Failure isolation
- Event replay

---

# Kafka vs RabbitMQ

**Question**

> Kafka vs RabbitMQ?

**Answer**

Kafka:

- Event streaming
- High throughput
- Message replay
- Distributed log
- Horizontal scaling

RabbitMQ:

- Traditional message broker
- Flexible routing
- Low latency messaging
- Work queues
- Request-response workflows

Kafka is generally preferred for large-scale event streaming.

---

# When Should You NOT Use Kafka?

**Question**

> When is Kafka not a good choice?

**Answer**

Kafka is not ideal for:

- Request-response communication
- Very small applications
- Simple task queues
- RPC
- Low-volume messaging

Kafka introduces operational complexity.

---

# Why Is Kafka Horizontally Scalable?

**Question**

> How does Kafka scale?

**Answer**

Kafka scales by:

- Adding brokers
- Adding partitions
- Adding consumers

Example:

```text
Broker 1

Broker 2

Broker 3
```

Traffic is distributed across the cluster.

---

# How Does Kafka Achieve High Availability?

**Question**

> How does Kafka remain available during failures?

**Answer**

Kafka uses:

- Replication
- ISR
- Leader Election

Example:

```text
Leader

↓

Follower

↓

Follower
```

If the leader fails, another replica becomes leader.

---

# Why Are Partitions Important?

**Question**

> Why does Kafka use partitions?

**Answer**

Partitions enable:

- Parallel processing
- Horizontal scaling
- Higher throughput

Without partitions:

```text
One Consumer

↓

One Partition
```

With partitions:

```text
Many Consumers

↓

Many Partitions
```

---

# Why Doesn't Kafka Guarantee Global Ordering?

**Question**

> Does Kafka guarantee message ordering?

**Answer**

Kafka guarantees ordering **only within a partition**.

Multiple partitions process data independently.

---

# How Do You Preserve Ordering?

**Question**

> How can related events remain ordered?

**Answer**

Use a message key.

Example:

```text
Order ID

↓

Hash

↓

Same Partition
```

All events for that order remain ordered.

---

# Explain Consumer Groups

**Question**

> Why are Consumer Groups important?

**Answer**

Consumer Groups allow parallel processing.

Example:

```text
Orders Topic

↓

Consumer Group

↓

Consumer A

Consumer B

Consumer C
```

Each partition is processed by one consumer within the group.

---

# What Happens When Traffic Doubles?

**Question**

> How would you scale Kafka?

**Answer**

Possible approaches:

- Add brokers
- Increase partitions
- Add consumers
- Tune producers

Scaling depends on the bottleneck.

---

# How Does Kafka Handle Failures?

**Question**

> What happens if a broker crashes?

**Answer**

Workflow:

```text
Leader Fails

↓

Leader Election

↓

Producer Retry

↓

Consumer Continues
```

Replication minimizes downtime.

---

# Why Is Kafka Durable?

**Question**

> How does Kafka prevent data loss?

**Answer**

Kafka provides durability through:

- Disk persistence
- Replication
- Acknowledgements
- ISR

Using:

```properties
acks=all
```

provides stronger durability.

---

# Explain Exactly Once Processing

**Question**

> How does Kafka achieve Exactly Once Processing?

**Answer**

Kafka combines:

- Idempotent Producers
- Transactions
- Offset coordination

This prevents duplicate processing in supported workflows.

---

# Why Is Kafka Good for Microservices?

**Question**

> Why is Kafka commonly used with microservices?

**Answer**

Benefits:

- Loose coupling
- Independent deployment
- Asynchronous communication
- Event replay
- High scalability

Each service can evolve independently.

---

# Explain a Real-World Kafka Architecture

**Question**

> Describe a production Kafka architecture.

**Answer**

Example:

```text
Users

↓

API Gateway

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

Email

↓

Analytics

↓

Data Warehouse
```

Kafka becomes the central event backbone.

---

# How Would You Design a Highly Available Kafka Cluster?

**Question**

> Design a highly available Kafka deployment.

**Answer**

Recommended:

- Minimum 3 brokers
- Replication Factor = 3
- `acks=all`
- `min.insync.replicas=2`
- SSL
- SASL
- ACLs
- Monitoring
- Backups

---

# How Would You Handle Millions of Messages Per Second?

**Question**

> How would you scale Kafka for very high throughput?

**Answer**

Approach:

- Increase partitions
- Add brokers
- Add consumers
- Enable batching
- Enable compression
- Use SSD/NVMe storage
- Monitor continuously

Scale horizontally rather than vertically whenever possible.

---

# Architecture Best Practices

**Question**

> What are Kafka architecture best practices?

**Answer**

- Design topics around business domains.
- Plan partitions carefully.
- Use Replication Factor = 3.
- Enable idempotence.
- Monitor Consumer Lag.
- Secure the cluster.
- Use Schema Registry.
- Design for failure.
- Automate infrastructure.
- Test disaster recovery regularly.

---

# Scenario-Based Questions

### Question

> A downstream service is unavailable. What happens?

**Answer**

Kafka stores messages until the consumer becomes available again.

Other consumers continue processing normally.

---

### Question

> One Consumer Group is very slow. Will other Consumer Groups be affected?

**Answer**

No.

Each Consumer Group maintains its own offsets and processes messages independently.

---

### Question

> Why shouldn't every microservice communicate through REST?

**Answer**

REST creates runtime dependencies.

Kafka allows asynchronous communication, improving resilience and scalability.

---

### Question

> Your application needs strict ordering for each customer. What would you do?

**Answer**

Use:

```text
Customer ID

↓

Message Key
```

This ensures all events for the same customer are routed to the same partition.

---

### Question

> How would you design Kafka for disaster recovery?

**Answer**

Use:

- Replication
- MirrorMaker 2
- Cross-region clusters
- Backups
- Tested recovery procedures

---

# Frequently Asked Interview Questions

- Why is Kafka used?
- Why is Kafka better than REST?
- Kafka vs RabbitMQ?
- Where does Kafka fit in microservices?
- Why are partitions important?
- How does Kafka scale?
- How does Kafka achieve High Availability?
- How does Kafka achieve durability?
- Why use Consumer Groups?
- How do you preserve message ordering?
- What is Event-Driven Architecture?
- How would you design a production Kafka cluster?
- How would you scale Kafka?
- When should Kafka not be used?
- How does Kafka support Exactly Once Processing?

---

# Summary

Kafka architecture questions evaluate a candidate's understanding of distributed systems, scalability, fault tolerance, and event-driven design rather than API-level knowledge. Strong interview answers should explain not only *how* Kafka works, but also *why* specific architectural decisions are made and what trade-offs they involve. Demonstrating real-world production experience with high availability, scalability, reliability, and microservices integration is often what differentiates senior engineers from junior developers.

---

# Key Takeaways

- Kafka is commonly used as the event backbone in distributed systems.
- It enables asynchronous communication and loose coupling between services.
- Partitions provide scalability, while replication provides fault tolerance.
- Consumer Groups enable parallel processing.
- Ordering is guaranteed only within a partition.
- Kafka is well suited for event-driven microservices and real-time data pipelines.
- Production architectures should emphasize monitoring, security, backups, and disaster recovery.
- Architecture questions focus on design decisions, trade-offs, and real-world deployment patterns rather than implementation details.