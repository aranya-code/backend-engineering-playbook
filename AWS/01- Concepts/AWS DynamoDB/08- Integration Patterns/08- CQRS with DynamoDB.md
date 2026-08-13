# 08 - CQRS with DynamoDB

## Overview

CQRS (Command Query Responsibility Segregation) is an architectural pattern that separates **write operations (Commands)** from **read operations (Queries)**.

Instead of using a single database model for both reading and writing, CQRS allows each side to be optimized independently.

Amazon DynamoDB is particularly well suited for CQRS because it offers:

- Extremely fast key-value lookups
- Flexible schema design
- Event-driven integration using DynamoDB Streams
- Horizontal scalability
- Low latency
- High throughput

In production systems, CQRS is often combined with:

- DynamoDB Streams
- AWS Lambda
- Amazon EventBridge
- Amazon SNS
- Amazon SQS
- Amazon OpenSearch
- Amazon ElastiCache (Redis)

---

# Learning Objectives

After completing this chapter, you'll understand:

- What CQRS is
- Why CQRS works well with DynamoDB
- Command vs Query models
- Read and write separation
- Event-driven synchronization
- Read model projection
- Production architectures
- Best practices
- Common pitfalls
- Interview questions

---

# What is CQRS?

CQRS separates application responsibilities into two independent models.

```text
               Application

              /           \

             /             \

      Command Model    Query Model
```

Instead of one model doing everything, each model is optimized for its specific purpose.

---

# Traditional CRUD Architecture

Traditional applications usually look like this:

```text
Users

↓

Application

↓

Database
```

The same tables handle:

- Inserts
- Updates
- Deletes
- Reads
- Reporting
- Analytics

As applications grow, this model becomes harder to optimize.

---

# CQRS Architecture

CQRS separates responsibilities.

```text
                  Users

             ┌─────────────┐

             ▼             ▼

       Write Requests   Read Requests

             │             │

             ▼             ▼

       Command API     Query API

             │             │

             ▼             ▼

      Write Database   Read Database
```

Each side can evolve independently.

---

# Commands

Commands modify state.

Examples:

```text
Create Order

Update Customer

Delete Product

Approve Payment

Reserve Inventory
```

Commands answer:

> **"Change something."**

---

# Queries

Queries retrieve information.

Examples:

```text
Get Order

Search Products

View Dashboard

Get Customer

Generate Reports
```

Queries answer:

> **"Read something."**

Queries should never modify data.

---

# Why DynamoDB Works Well

DynamoDB excels at predictable access patterns.

Example:

```text
Write Model

↓

Optimized for Transactions
```

```text
Read Model

↓

Optimized for Queries
```

Different table designs can be used for each workload.

---

# High-Level Architecture

```text
                 Client

           ┌───────────────┐

           ▼               ▼

     Command API      Query API

           │               │

           ▼               ▼

      Write Table      Read Table

           │

     DynamoDB Streams

           │

           ▼

        AWS Lambda

           │

           ▼

      Update Read Model
```

---

# Write Flow

```text
POST /orders

↓

Command API

↓

Validate

↓

Write DynamoDB

↓

Success
```

Only write operations occur here.

---

# Read Flow

```text
GET /orders/1001

↓

Query API

↓

Read Table

↓

Response
```

No writes occur during queries.

---

# Synchronizing Read Models

The read model is updated asynchronously.

```text
Write Table

↓

DynamoDB Streams

↓

Lambda

↓

Read Table
```

Applications never update the read model directly.

---

# Read Projection

The read model is often called a **Projection**.

Example:

Write table:

```text
Order

Customer

Items

Payments
```

Projection table:

```text
Order Summary

Order Status

Customer Name

Total Amount
```

The projection is optimized for API responses.

---

# Example

Customer places an order.

```text
Create Order

↓

Write Table

↓

Streams

↓

Lambda

↓

Order Summary Table
```

Dashboard queries become extremely fast.

---

# Search Optimization

Sometimes DynamoDB is not ideal for searching.

A common architecture:

```text
Write Table

↓

Streams

↓

Lambda

↓

Amazon OpenSearch
```

Users search OpenSearch while writes continue in DynamoDB.

---

# Analytics Projection

Business dashboards rarely query transactional tables directly.

Instead:

```text
Orders

↓

Streams

↓

Lambda

↓

Analytics Table
```

The analytics table contains precomputed aggregates.

---

# Eventual Consistency

CQRS introduces asynchronous updates.

```text
Write Complete

↓

Read Model Updating

↓

Eventually Consistent
```

There may be a short delay before queries reflect recent changes.

Applications must be designed with this expectation.

---

# Scaling Benefits

Reads and writes scale independently.

```text
Command Side

↑

Heavy Writes

────────────

Query Side

↑

Heavy Reads
```

Each side can be optimized separately.

---

# Error Handling

If projection updates fail:

```text
Streams

↓

Lambda

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Projection failures should not affect user writes.

---

# Monitoring

Monitor:

Command Side

- Write latency
- Failed writes
- Conditional failures

Query Side

- Read latency
- Cache hit rate
- Query performance

Projection Pipeline

- Stream processing delay
- Lambda errors
- DLQ messages

---

# Production Architecture

```text
                     Users

                        │

              Amazon API Gateway

             ┌──────────┴──────────┐

             ▼                     ▼

       Command Lambda        Query Lambda

             │                     │

             ▼                     ▼

      Orders Table         Order Summary Table

             │

      DynamoDB Streams

             │

             ▼

         AWS Lambda

             │

      ┌──────┼─────────┐

      ▼      ▼         ▼

Summary  OpenSearch  Analytics

      │

      ▼

 CloudWatch
```

---

# Performance Considerations

For high-scale CQRS systems:

- Keep command models normalized for consistency.
- Optimize read models for specific queries.
- Use GSIs only when appropriate.
- Avoid scanning transactional tables.
- Keep projections lightweight.
- Process stream events in batches.

---

# Security Best Practices

- Apply least-privilege IAM roles.
- Restrict write permissions to the command API.
- Allow read-only access to query services.
- Encrypt DynamoDB tables with AWS KMS.
- Enable CloudTrail auditing.
- Protect APIs using authentication and authorization.

---

# Best Practices

- Separate command and query responsibilities.
- Use DynamoDB Streams for synchronization.
- Design projections around access patterns.
- Accept eventual consistency.
- Keep read models disposable and rebuildable.
- Monitor projection lag.
- Build idempotent projection processors.
- Version event schemas.

---

# Common Mistakes

## Using the Same Table for Everything

```text
Users

↓

One Table

↓

Reads

Writes

Analytics

Search
```

As workloads grow, this becomes difficult to optimize.

---

## Expecting Immediate Consistency

CQRS typically relies on asynchronous updates.

Applications should tolerate short synchronization delays.

---

## Large Projection Logic

Projection services should only transform and publish data.

Avoid embedding unrelated business logic.

---

## Ignoring Failed Projections

Monitor stream processing and configure Dead Letter Queues for recovery.

---

# Production Considerations

Large-scale systems commonly combine:

```text
DynamoDB

↓

Streams

↓

Lambda

↓

EventBridge

↓

OpenSearch

↓

Redis

↓

CloudWatch
```

This architecture enables independent scaling of transactional processing, search, caching, and analytics while keeping services loosely coupled.

---

# Interview Notes

A common interview question is:

> **What is CQRS?**

CQRS (Command Query Responsibility Segregation) is an architectural pattern that separates write operations (commands) from read operations (queries), allowing each side to be independently optimized.

---

Another common question is:

> **Why is DynamoDB a good fit for CQRS?**

DynamoDB supports high-throughput transactional writes, flexible table design, and integrates with DynamoDB Streams, making it easy to build asynchronous read projections optimized for different query patterns.

---

Another common question is:

> **How are read models kept synchronized in DynamoDB CQRS?**

The write table emits change events through DynamoDB Streams. AWS Lambda consumes those events and updates one or more read-optimized projection tables or search indexes.

---

Another common question is:

> **What is the trade-off of CQRS?**

The primary trade-off is eventual consistency. Read models are updated asynchronously, so recently written data may not be immediately visible to query operations.

---

# Key Takeaways

- CQRS separates command (write) and query (read) responsibilities.
- DynamoDB's flexible schema and high throughput make it an excellent foundation for CQRS architectures.
- DynamoDB Streams and AWS Lambda are commonly used to synchronize read projections.
- Read models should be optimized for specific access patterns rather than mirroring the write model.
- CQRS improves scalability, maintainability, and performance, but applications must account for eventual consistency.