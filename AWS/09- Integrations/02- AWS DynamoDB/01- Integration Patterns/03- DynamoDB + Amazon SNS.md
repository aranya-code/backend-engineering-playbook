# 03 - DynamoDB + Amazon SNS

## Overview

Amazon DynamoDB and Amazon SNS (Simple Notification Service) are commonly integrated to build **event-driven systems** where a single database event can notify multiple independent services.

Unlike Amazon SQS, which is designed for **message queuing**, Amazon SNS is designed for **message broadcasting** using the Publish/Subscribe (Pub/Sub) model.

Whenever data changes in DynamoDB, applications can publish an event to an SNS topic. Multiple subscribers can then react independently without knowing about each other.

This architecture enables:

- Event-driven microservices
- Loose coupling
- Horizontal scalability
- High availability
- Easy integration with AWS services

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why DynamoDB and SNS are used together
- Publish/Subscribe architecture
- Fan-out messaging
- Event broadcasting
- SNS subscribers
- Error handling
- Reliability considerations
- Production architectures
- Best practices
- Interview questions

---

# Why Combine DynamoDB and SNS?

Suppose an order is created.

Without SNS:

```text
Order Service

↓

Send Email

↓

Update CRM

↓

Notify Warehouse

↓

Update Analytics

↓

Create Invoice
```

Every service must be called directly.

The Order Service becomes tightly coupled.

---

With SNS:

```text
Order Service

↓

Publish Event

↓

Amazon SNS

↓

All Subscribers Receive Event
```

Each service becomes independent.

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

           DynamoDB Table

                │

                ▼

         Publish to SNS Topic

                │

      ┌─────────┼─────────┐

      ▼         ▼         ▼

   Email     Billing   Inventory
```

---

# Common Use Cases

DynamoDB + SNS is commonly used for:

- Email notifications
- SMS alerts
- Order confirmations
- Payment notifications
- Cache invalidation
- Analytics pipelines
- CRM synchronization
- Event-driven microservices

---

# Pattern 1 — Order Notifications

Customer places an order.

```text
Create Order

↓

Store in DynamoDB

↓

Publish

↓

SNS Topic

↓

Subscribers
```

Subscribers:

- Email Service
- Inventory Service
- Billing Service
- Analytics Service

---

# Pattern 2 — User Registration

```text
User Created

↓

DynamoDB

↓

SNS

↓

Welcome Email

↓

CRM Update

↓

Analytics

↓

Audit Log
```

Every service receives the same event independently.

---

# Pattern 3 — Fan-Out Architecture

One event.

Multiple consumers.

```text
SNS Topic

       │

 ┌─────┼─────┐

 ▼     ▼     ▼

Email SMS Analytics
```

This is called the **Fan-Out Pattern**.

---

# Pattern 4 — Microservices

```text
Customer Service

↓

DynamoDB

↓

SNS

├── Notification Service

├── Billing Service

├── Fraud Detection

├── Inventory Service

└── Reporting Service
```

Services never communicate directly.

---

# How Events Flow

```text
Write Item

↓

Publish Event

↓

SNS Topic

↓

Deliver to Subscribers

↓

Business Processing
```

SNS simply broadcasts events.

---

# DynamoDB Streams + SNS

A common production architecture is:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

SNS

↓

Subscribers
```

The application only writes data.

Everything else happens automatically.

---

# Supported Subscribers

Amazon SNS can deliver messages to:

- AWS Lambda
- Amazon SQS
- HTTP endpoints
- HTTPS endpoints
- Email
- SMS
- Mobile push notifications

Example:

```text
SNS

├── Lambda

├── SQS

├── Email

└── HTTPS
```

---

# Message Structure

Typical event:

```json
{
  "eventType": "OrderCreated",
  "orderId": "ORD-10025",
  "customerId": "CUS-912",
  "timestamp": "2026-07-26T12:00:00Z"
}
```

Keep events focused on business facts rather than implementation details.

---

# Event Design

Good events describe:

```text
OrderCreated

PaymentCompleted

UserRegistered

InventoryUpdated
```

Avoid technical event names such as:

```text
DatabaseUpdated

PutItemExecuted

RecordModified
```

Business events are easier for consumers to understand.

---

# Message Filtering

SNS supports message filtering.

Example:

```text
SNS Topic

↓

OrderCreated

↓

Inventory Service

────────────

PaymentCompleted

↓

Billing Service
```

Each subscriber only receives relevant events.

---

# Error Handling

If a subscriber fails:

```text
SNS

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Configure retries and DLQs where supported.

---

# Ordering Considerations

Standard SNS topics:

- High throughput
- Best-effort ordering

FIFO SNS topics:

- Ordered delivery
- Exactly-once message deduplication (when configured correctly)

Choose based on business requirements.

---

# Monitoring

Monitor:

SNS

- Number of messages published
- Delivery failures
- Retry attempts
- DLQ usage

DynamoDB

- Streams health
- RCUs
- WCUs
- Latency
- Throttling

Lambda

- Invocation errors
- Duration
- Concurrent executions

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

                     Lambda

                        │

                        ▼

                    Amazon SNS

         ┌──────────────┼──────────────┐

         ▼              ▼              ▼

     Email        Inventory       Analytics

                        │

                        ▼

                   CloudWatch
```

---

# SNS vs SQS

| Amazon SNS | Amazon SQS |
|-------------|------------|
| Publish/Subscribe | Message Queue |
| One-to-many delivery | One consumer processes one message |
| Broadcast events | Buffer work |
| Fan-out architecture | Background processing |
| Push model | Pull model |

Many production systems use **SNS + SQS together**.

---

# SNS + SQS Fan-Out Pattern

```text
Order Created

↓

SNS Topic

↓

───────────────

Queue A

↓

Inventory Worker

───────────────

Queue B

↓

Billing Worker

───────────────

Queue C

↓

Analytics Worker
```

Benefits:

- Loose coupling
- Independent scaling
- Reliable delivery
- Failure isolation

This is one of the most common enterprise messaging patterns.

---

# Performance Considerations

For high-volume systems:

- Keep event payloads small.
- Include resource identifiers instead of large objects.
- Publish immutable events.
- Use message filtering.
- Monitor delivery failures.
- Design subscribers to be idempotent.

---

# Security Best Practices

- Encrypt SNS topics using AWS KMS.
- Restrict publishing permissions with IAM.
- Limit subscriptions using topic policies.
- Enable CloudTrail.
- Validate incoming events.
- Use HTTPS endpoints when integrating external systems.

---

# Best Practices

- Publish business events rather than database events.
- Keep messages immutable.
- Design subscribers to be independent.
- Use SNS for broadcasting.
- Combine SNS with SQS for reliable fan-out.
- Use DynamoDB Streams to automate event publishing.
- Monitor delivery metrics and failures.
- Keep payloads lightweight.

---

# Common Mistakes

## Calling Every Service Directly

Poor:

```text
Order Service

↓

Email

↓

Inventory

↓

Billing

↓

Analytics
```

Better:

```text
Order Service

↓

SNS

↓

Subscribers
```

---

## Sending Large Payloads

Avoid publishing entire database records.

Instead:

```text
OrderID

↓

Subscriber

↓

Lookup Data
```

---

## Coupling Subscribers

Subscribers should never depend on each other.

Each service should process events independently.

---

## Ignoring Failed Deliveries

Always configure retries and monitor failed deliveries.

---

# Production Considerations

Enterprise architectures often combine:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

SNS

↓

SQS

↓

Worker Services

↓

CloudWatch

↓

EventBridge
```

This provides:

- Loose coupling
- Horizontal scalability
- Reliable delivery
- Independent deployments
- Easier service evolution

---

# Interview Notes

A common interview question is:

> **Why integrate DynamoDB with Amazon SNS?**

SNS allows applications to broadcast events generated from DynamoDB changes to multiple independent services, enabling event-driven architectures and loose coupling.

---

Another common question is:

> **When should you use SNS instead of SQS?**

Use SNS when one event must be delivered to multiple subscribers. Use SQS when work needs to be buffered and processed by consumers asynchronously.

---

Another common question is:

> **Can DynamoDB publish directly to SNS?**

Not directly. A common architecture is **DynamoDB Streams → AWS Lambda → Amazon SNS**, where the Lambda function reads stream records and publishes business events to an SNS topic.

---

Another common question is:

> **Why are business events preferred over database events?**

Business events such as `OrderCreated` or `PaymentCompleted` are stable and meaningful to downstream services, whereas database operations like `PutItem` expose implementation details and tightly couple consumers to the database schema.

---

# Key Takeaways

- DynamoDB and Amazon SNS enable scalable publish/subscribe architectures.
- SNS broadcasts a single event to multiple independent subscribers.
- A common production pattern is **DynamoDB Streams → Lambda → SNS**.
- Use SNS for event broadcasting and combine it with SQS when reliable, independent processing is required.
- Design immutable business events, keep payloads lightweight, and build idempotent subscribers for resilient production systems.