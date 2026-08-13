# 04 - DynamoDB + Amazon EventBridge

## Overview

Amazon EventBridge is AWS's event bus service that enables applications to communicate using **events** instead of direct service-to-service calls.

When integrated with DynamoDB, EventBridge enables highly decoupled architectures where changes in DynamoDB trigger business workflows across multiple AWS services and external SaaS applications.

Unlike Amazon SNS, which focuses on broadcasting messages, EventBridge provides:

- Event routing
- Content-based filtering
- Schema discovery
- Multiple event buses
- SaaS integrations
- Workflow orchestration

A common production architecture is:

```text
DynamoDB

↓

DynamoDB Streams

↓

AWS Lambda

↓

Amazon EventBridge

↓

Multiple Event Consumers
```

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why integrate DynamoDB with EventBridge
- Event bus architecture
- Event routing
- Rule-based event filtering
- EventBridge vs SNS vs SQS
- Event-driven microservices
- Production architectures
- Best practices
- Interview questions

---

# Why Use EventBridge?

Modern applications consist of many independent services.

Without EventBridge:

```text
Order Service

↓

Inventory

↓

Billing

↓

Shipping

↓

Notifications

↓

Analytics
```

Every service knows about every other service.

As the system grows, maintenance becomes increasingly difficult.

---

With EventBridge:

```text
Order Service

↓

EventBridge

↓

Routing Rules

↓

Interested Services
```

Services only publish events.

They never need to know who consumes them.

---

# High-Level Architecture

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

             Backend Service

                   │

                   ▼

             DynamoDB Table

                   │

            DynamoDB Streams

                   │

                   ▼

               AWS Lambda

                   │

                   ▼

            Amazon EventBridge

       ┌───────────┼───────────┐

       ▼           ▼           ▼

   Billing     Inventory    Analytics
```

---

# Event Flow

```text
Application

↓

PutItem()

↓

DynamoDB

↓

Streams

↓

Lambda

↓

EventBridge

↓

Business Services
```

The application performs only the database write.

Everything else is asynchronous.

---

# Common Use Cases

EventBridge is commonly used for:

- Order processing
- Inventory updates
- Payment workflows
- User onboarding
- Fraud detection
- Compliance auditing
- Notification systems
- Workflow orchestration
- Multi-account communication

---

# Pattern 1 — Order Processing

```text
Order Created

↓

DynamoDB

↓

Streams

↓

Lambda

↓

EventBridge

↓

Billing

↓

Shipping

↓

Inventory
```

Each service reacts independently.

---

# Pattern 2 — User Registration

```text
User Created

↓

EventBridge

↓

Welcome Email

↓

CRM

↓

Analytics

↓

Audit Logs
```

The user service remains completely unaware of downstream systems.

---

# Pattern 3 — Multi-Service Routing

```text
OrderCreated Event

↓

EventBridge

├── Inventory Service

├── Shipping Service

├── Billing Service

├── Analytics Service

└── Fraud Detection
```

Every service receives only the events it needs.

---

# EventBridge Rules

One of EventBridge's biggest advantages is intelligent routing.

Example:

```text
Event Type

↓

OrderCreated

↓

Billing Rule

↓

Billing Service
```

Another rule:

```text
Event Type

↓

InventoryUpdated

↓

Analytics Rule
```

Different rules can process the same event independently.

---

# Content-Based Filtering

Rules can inspect event payloads.

Example:

```json
{
  "eventType": "OrderCreated",
  "amount": 1200,
  "country": "US"
}
```

Rule:

```text
amount > 1000

↓

Fraud Detection
```

Only high-value orders trigger fraud analysis.

---

# Event Structure

Typical business event:

```json
{
  "source": "orders-service",
  "detail-type": "OrderCreated",
  "detail": {
    "orderId": "ORD-101",
    "customerId": "CUS-50",
    "amount": 299.99
  }
}
```

Use business-oriented events instead of database terminology.

---

# EventBridge vs SNS

| EventBridge | SNS |
|-------------|-----|
| Event routing | Event broadcasting |
| Rule-based filtering | Topic-based delivery |
| Complex routing | Simple Pub/Sub |
| SaaS integrations | Notifications |
| Event buses | Topics |

---

# EventBridge vs SQS

| EventBridge | SQS |
|-------------|-----|
| Event router | Message queue |
| Push delivery | Pull model |
| Multiple consumers | Worker processing |
| Event orchestration | Job processing |

---

# EventBridge vs DynamoDB Streams

| DynamoDB Streams | EventBridge |
|------------------|-------------|
| Captures database changes | Routes business events |
| 24-hour retention | Event routing service |
| Database specific | Application-wide integration |
| Item-level events | Business events |

They complement each other rather than compete.

---

# Multi-Account Architecture

Large enterprises often use multiple AWS accounts.

```text
Account A

↓

EventBridge

↓

Account B

↓

Billing Service

↓

Account C

↓

Analytics
```

This enables secure event sharing across accounts.

---

# Schema Registry

EventBridge can automatically discover event schemas.

Benefits:

- Strong typing
- Code generation
- Better documentation
- Easier integration

---

# Error Handling

If a target fails:

```text
Event

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Configure DLQs for critical workflows.

---

# Monitoring

Monitor:

EventBridge

- Failed invocations
- Successful invocations
- Rule matches
- Delivery latency

Lambda

- Errors
- Duration
- Retries

DynamoDB

- Streams health
- Throttling
- Latency

---

# Production Architecture

```text
                   Users

                      │

                API Gateway

                      │

                      ▼

              Backend Service

                      │

                      ▼

                DynamoDB Table

                      │

               DynamoDB Streams

                      │

                      ▼

                 AWS Lambda

                      │

                      ▼

              Amazon EventBridge

      ┌───────────────┼────────────────┐

      ▼               ▼                ▼

 Billing        Fraud Detection    Inventory

      ▼

 Notifications

      ▼

 CloudWatch
```

---

# Performance Considerations

For high-volume systems:

- Keep events small.
- Publish immutable events.
- Avoid large payloads.
- Use EventBridge rules instead of application logic.
- Route only required events.
- Archive events if needed.
- Monitor failed deliveries.

---

# Security Best Practices

- Use IAM least privilege.
- Encrypt sensitive payloads.
- Enable CloudTrail.
- Restrict event bus permissions.
- Validate incoming events.
- Use custom event buses for application isolation.

---

# Best Practices

- Publish business events instead of CRUD events.
- Keep producers unaware of consumers.
- Use meaningful event names.
- Design immutable event payloads.
- Filter events using EventBridge rules.
- Monitor failures continuously.
- Configure DLQs.
- Version event schemas.

---

# Common Mistakes

## Publishing Database Events Directly

Poor:

```text
PutItemExecuted
```

Better:

```text
OrderCreated
```

Business events are stable and meaningful.

---

## Large Event Payloads

Publish identifiers instead.

```text
OrderID

↓

Consumer

↓

Retrieve Details
```

---

## Tight Coupling

Producers should never know which services consume events.

---

## No Dead Letter Queue

Always configure DLQs for critical integrations.

---

# Production Considerations

Enterprise architectures frequently combine:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

EventBridge

↓

SQS

↓

SNS

↓

Step Functions

↓

CloudWatch
```

This creates an event-driven platform capable of handling millions of events per day while remaining loosely coupled and highly scalable.

---

# Interview Notes

A common interview question is:

> **Why use EventBridge with DynamoDB?**

EventBridge enables business events generated from DynamoDB changes to be routed intelligently to multiple services without tightly coupling producers and consumers.

---

Another common question is:

> **How is EventBridge different from SNS?**

SNS broadcasts messages to all subscribers of a topic. EventBridge uses rules to selectively route events to specific targets based on event content.

---

Another common question is:

> **Can DynamoDB publish directly to EventBridge?**

Not directly. The common architecture is:

```text
DynamoDB Streams

↓

AWS Lambda

↓

Amazon EventBridge
```

The Lambda function converts database changes into business events and publishes them to EventBridge.

---

Another common question is:

> **When should you choose EventBridge over SNS?**

Choose EventBridge when you need intelligent event routing, content-based filtering, workflow orchestration, SaaS integrations, or cross-account event delivery. Choose SNS when you simply need to broadcast notifications to multiple subscribers.

---

# Key Takeaways

- EventBridge is an intelligent event router that complements DynamoDB Streams.
- A common architecture is **DynamoDB Streams → Lambda → EventBridge**.
- EventBridge enables loosely coupled, event-driven microservices through rule-based routing.
- Publish business events rather than database operations to keep services independent.
- Configure monitoring, retries, DLQs, and schema versioning to build reliable production event-driven systems.