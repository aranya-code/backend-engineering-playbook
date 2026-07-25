# 09 - System Design Scenarios

## Overview

This chapter focuses on **system design interview questions** where DynamoDB is one component of a larger distributed system.

Senior backend interviews rarely ask:

> "What is DynamoDB?"

Instead they ask:

> "Design Instagram."
>
> "Design Uber."
>
> "Design Amazon Shopping Cart."
>
> "Design a Notification System."

Your ability to decide **when DynamoDB should be used—and when it shouldn't—is far more important than memorizing APIs.**

---

# Learning Objectives

After completing this chapter, you'll be able to discuss:

- System design decisions
- Database selection
- High-scale architecture
- Hot partition mitigation
- Event-driven architecture
- Caching strategies
- Global deployments
- Production trade-offs

---

# Scenario 1

## Design a URL Shortener (TinyURL)

### Requirements

- Short URL generation
- Redirect in milliseconds
- Billions of URLs
- High availability

---

## High-Level Design

```text
          Client
             │
             ▼
      Load Balancer
             │
             ▼
        API Service
             │
             ▼
        DynamoDB
      PK = ShortCode
```

---

### DynamoDB Schema

```text
PK

abc123
```

Attributes

```text
OriginalURL

CreatedAt

ExpiresAt

Clicks
```

---

### Why DynamoDB?

Advantages

- Extremely fast lookups
- Predictable latency
- Horizontal scaling
- Simple key-value access

---

### Interview Follow-up

How would you expire links?

Answer:

```text
TTL
```

---

# Scenario 2

## Design an E-commerce Shopping Cart

Requirements

- Millions of users
- Low latency
- Multiple devices
- High availability

---

### Schema

```text
PK

USER#100
```

```text
SK

CART#ITEM1

CART#ITEM2

CART#ITEM3
```

---

Architecture

```text
User

↓

API

↓

DynamoDB

↓

Streams

↓

Inventory Update

↓

Lambda
```

---

Why DynamoDB?

- Fast lookups
- Session-style data
- Horizontal scaling

---

# Scenario 3

## Design a Notification Service

Requirements

- Millions of notifications
- Event-driven
- Asynchronous processing

---

Architecture

```text
Application

↓

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

Notification Workers
```

---

Advantages

- Loose coupling
- Retry support
- Independent scaling
- Event-driven

---

# Scenario 4

## Design an Order Management System

Requirements

- Orders
- Payments
- Shipments
- Tracking

---

Schema

```text
PK

ORDER#1001
```

Sort Keys

```text
ORDER

PAYMENT

SHIPMENT

TRACKING
```

---

Architecture

```text
API

↓

DynamoDB

↓

Streams

↓

Billing

↓

Inventory

↓

Shipping
```

---

Benefits

- Single Query
- No joins
- High throughput

---

# Scenario 5

## Design a Leaderboard

Requirements

- Millions of scores
- Top 100 players
- Frequent updates

---

Should DynamoDB be used?

Answer

Yes—with a GSI.

Example

```text
PK

GameID
```

GSI

```text
Score
```

---

Potential Problem

Frequent updates

↓

Write amplification

↓

Higher costs

---

Possible Improvement

Use Redis for real-time ranking

↓

Persist periodically into DynamoDB

---

# Scenario 6

## Design a Chat Application

Requirements

- Billions of messages
- Ordered messages
- Low latency

---

Schema

```text
PK

CHAT#100
```

Sort Key

```text
Timestamp
```

---

Architecture

```text
Client

↓

API

↓

DynamoDB

↓

Streams

↓

Notification Service
```

---

Optimization

Latest messages

↓

Query

↓

Descending order

---

# Scenario 7

## Design an IoT Telemetry Platform

Requirements

- Millions of devices
- Continuous writes
- Time-series queries

---

Schema

```text
PK

DEVICE#100
```

Sort Key

```text
Timestamp
```

---

Architecture

```text
IoT Devices

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

Streams

↓

Analytics
```

---

Interview Discussion

How would you archive old data?

Answer

```text
TTL

↓

Lambda

↓

Amazon S3
```

---

# Scenario 8

## Design a Banking Transaction System

Should DynamoDB be used?

---

Expected Answer

It depends.

Good candidates discuss trade-offs.

Use DynamoDB when

- High scalability
- Account lookups
- User profiles
- Session data

Use relational databases when

- Complex financial transactions
- Cross-account consistency
- Regulatory reporting
- Complex joins

---

Interview Tip

Never answer

> "Use DynamoDB for everything."

---

# Scenario 9

## Design a Multi-Region Application

Requirements

- Global users
- Low latency
- Disaster recovery

---

Architecture

```text
US-East-1

↓

Global Tables

↓

EU-West-1

↓

Global Tables

↓

AP-South-1
```

---

Benefits

- Low latency
- Automatic replication
- Regional resilience

---

Challenges

- Conflict resolution
- Cross-region writes
- Eventual consistency
- Regulatory compliance

---

# Scenario 10

## Design a High-Traffic Product Catalog

Requirements

- Millions of reads
- Rare updates

---

Architecture

```text
Users

↓

CloudFront

↓

API

↓

Redis

↓

DynamoDB
```

---

Benefits

- Low database load
- Lower costs
- Faster response times

---

# Scenario 11

## Design a Real-Time Analytics Pipeline

Architecture

```text
Application

↓

DynamoDB

↓

Streams

↓

Lambda

↓

Kinesis

↓

Analytics

↓

Data Lake
```

---

Purpose

- Event collection
- Business analytics
- Dashboards
- Machine learning

---

# Scenario 12

## Design a Highly Available Session Store

Requirements

- Millions of logins
- Automatic expiration
- Low latency

---

Schema

```text
PK

SESSION#UUID
```

Attributes

```text
UserID

ExpiresAt

Token
```

---

TTL

```text
Automatic Cleanup
```

---

Perfect Use Case

- Login sessions
- JWT metadata
- Temporary authentication

---

# Rapid Fire System Design Questions

| Scenario | Recommended Solution |
|----------|----------------------|
| URL Shortener | DynamoDB + TTL |
| Shopping Cart | Single Table |
| Chat Messages | PK + Timestamp |
| IoT Platform | Time-Series Design |
| Global App | Global Tables |
| Session Store | TTL |
| Notification System | Streams + Lambda |
| Analytics | Streams + Kinesis |
| Product Catalog | Redis + DynamoDB |
| Banking | Depends on requirements |

---

# Senior Interview Tips

A strong answer follows this structure:

```text
Requirements

↓

Traffic Estimate

↓

Database Choice

↓

Schema Design

↓

Scaling Strategy

↓

Caching

↓

Failure Handling

↓

Monitoring

↓

Trade-offs
```

Discuss:

- Read/write patterns
- Latency requirements
- Data consistency
- Failure recovery
- Operational complexity
- Cost optimization

---

# Common Mistakes

## Choosing DynamoDB Without Justification

Always explain **why** DynamoDB fits the workload instead of assuming it is the default choice.

---

## Ignoring Access Patterns

Schema design should begin with expected queries, not entities.

---

## Forgetting Caching

For read-heavy systems, services like Amazon ElastiCache (Redis) can significantly reduce latency and DynamoDB read costs.

---

## Ignoring Failure Scenarios

Discuss:

- Regional failures
- Retry strategies
- Dead-letter queues
- Monitoring
- Disaster recovery

---

# Interview Cheat Sheet

```text
Requirements

↓

Access Patterns

↓

Database Selection

↓

Schema Design

↓

Indexes

↓

Caching

↓

Streams

↓

Scaling

↓

Monitoring

↓

Trade-offs
```

---

# Key Takeaways

- Senior system design interviews evaluate architectural reasoning rather than API knowledge.
- DynamoDB excels in workloads requiring predictable low latency, horizontal scalability, and access-pattern-driven design.
- Successful designs often combine DynamoDB with complementary AWS services such as Lambda, SNS, SQS, ElastiCache, Kinesis, and Global Tables.
- Every architectural decision should be justified by discussing scalability, availability, consistency, cost, and operational complexity.
- The strongest candidates explain not only **why** DynamoDB is appropriate but also **when another database would be a better choice**.