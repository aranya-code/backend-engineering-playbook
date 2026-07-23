# 25 - Best Practices and Anti-Patterns

## Overview

Building a DynamoDB application is not difficult.

Building a **highly scalable, cost-efficient, fault-tolerant DynamoDB application** is.

Unlike traditional relational databases, DynamoDB rewards applications that are designed around its architecture. Most production issues arise not because DynamoDB cannot scale, but because the data model was designed as if DynamoDB were a relational database.

This chapter consolidates the lessons from previous chapters into a practical guide for designing production-ready DynamoDB systems.

---

# Think in Access Patterns, Not Tables

One of the biggest mindset shifts when moving from SQL to DynamoDB is changing **how data is modeled**.

### Relational Database

```text
Design Tables

↓

Normalize Data

↓

Write SQL Queries
```

### DynamoDB

```text
Identify Access Patterns

↓

Design Keys

↓

Store Data Accordingly
```

Before creating a table, answer:

- What queries will the application execute?
- How will users retrieve data?
- Which operations are most frequent?
- What latency is acceptable?

The schema should support these access patterns directly.

---

# Design High-Cardinality Partition Keys

The partition key determines how data is distributed.

Good example:

```text
CustomerId

OrderId

SessionId

InvoiceId
```

Poor example:

```text
Country

Status

Department

Region
```

Low-cardinality keys concentrate requests onto a few partitions, causing throttling.

---

# Prefer Query Over Scan

A **Query** retrieves only the required partition.

```text
Partition

↓

Read Matching Items
```

A **Scan** examines every partition.

```text
Partition 1

↓

Partition 2

↓

Partition 3

↓

...

↓

Entire Table
```

Always ask:

> Can this operation be converted into a Query?

If the answer is yes, it almost always should be.

---

# Avoid Hot Partitions

Even if a table has millions of RCUs and WCUs, one overloaded partition can still throttle requests.

Example:

```text
Partition Key

Today'sDate
```

Every request hits the same partition.

Better:

```text
OrderId

CustomerId

SessionId
```

Distribute traffic evenly.

---

# Denormalize Intelligently

Normalization reduces redundancy.

DynamoDB favors redundancy to reduce query complexity.

Instead of:

```text
Customer Table

↓

JOIN

↓

Orders Table
```

Store frequently accessed information together.

```text
Order

↓

CustomerName

CustomerTier

ShippingAddress
```

Storage is inexpensive.

Network round trips are not.

---

# Minimize Secondary Indexes

Each Global Secondary Index (GSI):

- Consumes write capacity
- Increases storage
- Adds replication work
- Increases cost

Before creating an index, ask:

> Is this access pattern essential?

Only create indexes for frequently executed queries.

---

# Keep Items Small

Although DynamoDB supports items up to **400 KB**, smaller items offer:

- Faster reads
- Faster writes
- Lower RCU consumption
- Lower WCU consumption
- Better cache efficiency

Large blobs should typically be stored in Amazon S3, with only references stored in DynamoDB.

---

# Use Conditional Writes

Prevent race conditions with conditional expressions.

Example:

```text
Update Balance

Only If

Version = 5
```

Benefits:

- Prevents lost updates
- Supports optimistic locking
- Avoids accidental overwrites

---

# Enable Point-in-Time Recovery

Every production table should enable PITR.

Benefits:

- Recover from accidental deletion
- Recover from application bugs
- Reduce Recovery Point Objective (RPO)
- Simplify disaster recovery

The cost of PITR is usually far less than the cost of data loss.

---

# Monitor Everything

Use CloudWatch to monitor:

- Consumed RCUs
- Consumed WCUs
- Throttled Requests
- System Errors
- Latency
- Auto Scaling Events

Monitoring should be proactive, not reactive.

---

# Secure Every Table

Security is more than encryption.

Production systems should include:

- IAM Roles
- Least privilege
- KMS encryption
- TLS
- CloudTrail
- VPC Endpoints
- CloudWatch alarms

Security should be built into the architecture from the beginning.

---

# Plan for Failure

Applications should assume failures will occur.

Examples:

- Region outages
- Deployment bugs
- Accidental deletion
- Traffic spikes
- Hardware failures

Combine:

```text
PITR

+

Backups

+

CloudWatch

+

Auto Scaling

+

Global Tables
```

to improve resilience.

---

# Optimize for Cost

Common cost optimization techniques include:

- Prefer Query over Scan.
- Remove unused GSIs.
- Enable Auto Scaling.
- Choose On-Demand for unpredictable workloads.
- Use Provisioned Capacity for stable workloads.
- Archive historical data to Amazon S3.
- Use TTL for temporary data.

Performance and cost should be balanced.

---

# Common Anti-Patterns

## Treating DynamoDB Like SQL

Trying to recreate joins and normalized schemas often leads to inefficient designs.

---

## Designing Before Knowing Access Patterns

Schema-first thinking works poorly in DynamoDB.

Always start with access patterns.

---

## Using Scan in Production APIs

Scans are expensive and slow.

Production APIs should primarily use Query operations.

---

## Ignoring Hot Partitions

A table can have abundant capacity yet still experience throttling if traffic is concentrated on a single partition.

---

## Creating Too Many GSIs

Indexes improve flexibility but increase storage, write costs, and operational complexity.

---

## Using Sequential Partition Keys

Example:

```text
Order-1

Order-2

Order-3
```

Sequential keys often create uneven traffic distribution.

Prefer randomly distributed or naturally diverse identifiers.

---

## Storing Large Binary Objects

Do not store images, videos, or documents directly in DynamoDB.

Instead:

```text
Amazon S3

↓

Object URL

↓

DynamoDB Reference
```

---

## Hardcoding AWS Credentials

Never embed:

```text
AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY
```

Use IAM Roles instead.

---

# Production Readiness Checklist

Before deploying a DynamoDB-backed application, verify:

- High-cardinality partition keys
- Query-based access patterns
- No unnecessary scans
- Appropriate GSIs
- Auto Scaling configured
- PITR enabled
- Backups configured
- IAM least privilege enforced
- Encryption enabled
- CloudWatch alarms configured
- CloudTrail enabled
- Recovery procedures documented
- Load testing completed

---

# Real-World Example

An online retail platform prepares for Black Friday.

Instead of simply increasing table capacity, the engineering team:

- Reviews access patterns.
- Verifies partition key distribution.
- Removes unnecessary scans.
- Enables Auto Scaling.
- Enables PITR.
- Configures CloudWatch alarms.
- Validates Global Tables.
- Performs load testing.

The focus is on architecture rather than simply allocating more resources.

---

# Architecture Perspective

A mature production deployment typically looks like:

```text
Users

↓

API Gateway

↓

Lambda / ECS

↓

IAM Roles

↓

DynamoDB

├── High-Cardinality Partition Keys
├── Query-Based Access
├── Auto Scaling
├── Adaptive Capacity
├── PITR
├── Encryption
├── CloudWatch
└── CloudTrail

↓

Amazon S3 (Archives)

↓

Analytics Pipeline
```

Every component contributes to scalability, reliability, security, or operational visibility.

---

# Interview Notes

A common interview question is:

> **What are the biggest mistakes developers make when using DynamoDB?**

Typical answers include:

- Designing schemas before identifying access patterns.
- Using Scan instead of Query.
- Choosing poor partition keys.
- Overusing Global Secondary Indexes.
- Ignoring monitoring and throttling metrics.
- Treating DynamoDB like a relational database.

Another common question is:

> **What would you review before approving a DynamoDB design for production?**

A senior engineer should evaluate:

- Partition key selection
- Access patterns
- Capacity mode
- Index design
- Recovery strategy
- Security configuration
- Monitoring and alerting
- Cost implications
- Scalability under peak load
- Operational runbooks

---

# Senior Backend Engineering Checklist

Before approving a DynamoDB design, ask yourself:

- Can every API endpoint use `Query` instead of `Scan`?
- Are partition keys evenly distributing traffic?
- Is the data model driven by access patterns?
- Are GSIs truly necessary?
- Have I minimized item size?
- Are conditional writes protecting against concurrent updates?
- Is PITR enabled?
- Are backups tested?
- Are IAM permissions least-privileged?
- Can this design scale 100× without changing the schema?

If the answer to most of these questions is **yes**, the design is likely ready for production.

---

# Key Takeaways

- DynamoDB is optimized for **access-pattern-driven design**, not relational modeling.
- High-cardinality partition keys are essential for scalability.
- Prefer `Query` over `Scan` whenever possible.
- Keep items small and denormalize thoughtfully.
- Use GSIs sparingly and only for well-defined access patterns.
- Protect production data with PITR, backups, encryption, and least-privilege IAM.
- Monitor capacity, latency, and throttling with CloudWatch.
- Production success depends as much on architecture and operational practices as on API usage.
- Designing with DynamoDB's distributed architecture in mind results in systems that are scalable, resilient, and cost-efficient.