# 09 - Event-Driven Microservices

## Overview

Modern distributed systems are increasingly built using **event-driven microservices**, where services communicate by publishing and consuming events instead of calling each other directly.

Amazon DynamoDB plays a central role in this architecture by acting as the transactional data store, while services communicate asynchronously using:

- DynamoDB Streams
- Amazon EventBridge
- Amazon SNS
- Amazon SQS
- AWS Lambda

Instead of tightly coupled synchronous APIs, services exchange **business events**.

Typical events include:

- OrderCreated
- PaymentCompleted
- InventoryReserved
- ShipmentDispatched
- CustomerRegistered

This architecture provides:

- Loose coupling
- Independent deployments
- Horizontal scalability
- Fault isolation
- Better resilience
- High availability

---

# Learning Objectives

After completing this chapter, you'll understand:

- What event-driven microservices are
- Why DynamoDB is commonly used in this architecture
- Event publishing patterns
- Event consumption patterns
- Service ownership
- Eventual consistency
- Production architectures
- Best practices
- Common mistakes
- Interview questions

---

# Traditional Microservices

Without events, services call one another directly.

```text
Order Service

↓

Payment Service

↓

Inventory Service

↓

Shipping Service

↓

Notification Service
```

Problems:

- Tight coupling
- Cascading failures
- Long response times
- Difficult deployments
- Complex dependency management

---

# Event-Driven Architecture

Instead of direct communication:

```text
Order Service

↓

Publish Event

↓

Event Bus

↓

Interested Services
```

Every service works independently.

---

# High-Level Architecture

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

                  DynamoDB

                      │

              DynamoDB Streams

                      │

                      ▼

                  AWS Lambda

                      │

                      ▼

                 EventBridge

       ┌──────────────┼──────────────┐

       ▼              ▼              ▼

 Payment Service  Inventory     Analytics

       ▼

 Notification Service
```

---

# Service Ownership

Each microservice owns its own database.

```text
Order Service

↓

Orders Table

────────────

Inventory Service

↓

Inventory Table

────────────

Payment Service

↓

Payments Table
```

Services never modify another service's database directly.

---

# Why Database Sharing Is Bad

Avoid:

```text
Service A

↓

Shared Database

↑

Service B
```

Problems:

- Tight coupling
- Schema conflicts
- Deployment risks
- Hidden dependencies

Instead:

```text
Each Service

↓

Own Database

↓

Publish Events
```

---

# Business Events

Good event names describe business actions.

Examples:

```text
OrderCreated

OrderCancelled

PaymentSucceeded

InventoryReserved

ShipmentDelivered
```

Avoid technical events:

```text
RowInserted

PutItemExecuted

UpdateCompleted
```

Business events remain stable even if implementation changes.

---

# Event Flow

Customer places an order.

```text
Create Order

↓

Orders Table

↓

Streams

↓

Lambda

↓

EventBridge

↓

Subscribers
```

Subscribers may include:

- Payment Service
- Inventory Service
- Notification Service
- Analytics Service

---

# Event Choreography

Each service reacts independently.

```text
OrderCreated

↓

Payment Service

↓

PaymentCompleted

↓

Inventory Service

↓

InventoryReserved

↓

Shipping Service
```

There is no central controller.

---

# Event Orchestration

Sometimes a central workflow is required.

```text
Step Functions

↓

Order

↓

Payment

↓

Inventory

↓

Shipping
```

Use orchestration when business processes require coordination.

---

# Eventual Consistency

Each service updates independently.

```text
Order Created

↓

Payment Pending

↓

Inventory Pending

↓

Shipping Pending

↓

Eventually Complete
```

Temporary differences between services are expected.

---

# Idempotent Consumers

Events may be delivered more than once.

```text
Event

↓

Consumer

↓

Duplicate Event

↓

Ignore
```

Consumers should safely process duplicate events.

Common techniques:

- Event IDs
- Deduplication tables
- Conditional writes
- Idempotency keys

---

# Failure Recovery

Suppose Inventory Service is unavailable.

```text
Event

↓

Queue

↓

Retry

↓

Success
```

The Order Service continues functioning.

This isolation is a major advantage of event-driven systems.

---

# Saga Pattern

Distributed transactions are replaced with compensating actions.

```text
Order Created

↓

Payment Successful

↓

Inventory Failed

↓

Refund Payment

↓

Cancel Order
```

The Saga Pattern ensures eventual business consistency.

---

# Monitoring Event Pipelines

Monitor:

- Published events
- Failed events
- Retry counts
- DLQ size
- Consumer latency
- Processing duration
- Stream lag

Use:

- CloudWatch
- AWS X-Ray
- CloudTrail

---

# Production Architecture

```text
                      Users

                         │

                  API Gateway

                         │

                         ▼

                  Order Service

                         │

                    DynamoDB

                         │

                DynamoDB Streams

                         │

                         ▼

                     AWS Lambda

                         │

                         ▼

                   EventBridge

       ┌─────────────┼─────────────┐

       ▼             ▼             ▼

 Payment      Inventory      Notification

       ▼

    Amazon SQS

       ▼

 Retry Workers

       ▼

 CloudWatch
```

---

# Scaling Microservices

Every service scales independently.

```text
Orders

↓

10 Instances

────────────

Inventory

↓

4 Instances

────────────

Payments

↓

20 Instances
```

Scaling decisions are based on each service's workload.

---

# Performance Considerations

For production systems:

- Publish small events.
- Use immutable event payloads.
- Keep services stateless.
- Batch processing where appropriate.
- Avoid synchronous dependencies.
- Scale consumers independently.
- Use asynchronous retries.

---

# Security Best Practices

- Encrypt DynamoDB tables using AWS KMS.
- Secure EventBridge with IAM policies.
- Encrypt SNS/SQS messages where applicable.
- Enable CloudTrail auditing.
- Validate event payloads.
- Authenticate API requests before publishing events.

---

# Best Practices

- Each service owns its data.
- Publish business events instead of database events.
- Keep services loosely coupled.
- Design idempotent consumers.
- Accept eventual consistency.
- Monitor event processing continuously.
- Use DLQs for failed messages.
- Version event schemas.

---

# Common Mistakes

## Shared Databases

```text
Service A

↓

Shared Database

↑

Service B
```

Avoid shared persistence between services.

---

## Synchronous Chains

Poor:

```text
Order

↓

Payment

↓

Inventory

↓

Shipping
```

Better:

```text
Order

↓

Publish Event

↓

Independent Consumers
```

---

## Large Events

Avoid sending full database records.

Instead:

```text
OrderID

↓

Consumer

↓

Retrieve Details
```

---

## No Retry Strategy

Distributed systems experience transient failures.

Always configure retries and Dead Letter Queues.

---

## Ignoring Event Versioning

Events evolve over time.

Use versioned event schemas to support backward compatibility.

---

# Production Considerations

Enterprise systems commonly combine:

```text
API Gateway

↓

Lambda

↓

DynamoDB

↓

Streams

↓

EventBridge

↓

SNS

↓

SQS

↓

Step Functions

↓

CloudWatch

↓

AWS X-Ray
```

This architecture enables loosely coupled services that can evolve and scale independently while maintaining high reliability.

---

# Interview Notes

A common interview question is:

> **What are event-driven microservices?**

Event-driven microservices communicate by publishing and consuming events rather than making direct synchronous API calls. This improves scalability, resilience, and loose coupling.

---

Another common question is:

> **Why is DynamoDB a good choice for event-driven architectures?**

DynamoDB provides low-latency, highly scalable storage and integrates with DynamoDB Streams, making it easy to publish data changes as events for downstream processing.

---

Another common question is:

> **What is the difference between choreography and orchestration?**

In choreography, each service reacts independently to events without a central coordinator. In orchestration, a central workflow engine (such as AWS Step Functions) controls the sequence of operations.

---

Another common question is:

> **Why is idempotency important in event-driven systems?**

Messaging systems can deliver duplicate events. Idempotent consumers ensure that processing the same event multiple times does not produce incorrect or inconsistent results.

---

# Key Takeaways

- Event-driven microservices communicate through business events instead of direct service calls.
- DynamoDB Streams, Lambda, and EventBridge provide a common foundation for event propagation.
- Each microservice should own its own database and publish events when state changes.
- Design for eventual consistency, retries, idempotency, and fault isolation.
- Combining DynamoDB with EventBridge, SNS, SQS, and Step Functions enables scalable, resilient, production-grade distributed systems.