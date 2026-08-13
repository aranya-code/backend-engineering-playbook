# 03 - Slow Queries & Poor Performance

## Overview

One of the biggest misconceptions about DynamoDB is that it is "always fast."

DynamoDB is capable of **single-digit millisecond latency**, but achieving that performance depends entirely on good data modeling and access patterns.

When applications become slow, the root cause is rarely DynamoDB itself. Instead, it is usually caused by:

- Poor partition key design
- Scan operations
- Large partitions
- Hot partitions
- Inefficient GSIs
- Excessive network calls
- Large item sizes
- Client-side inefficiencies

This chapter explores how to identify, troubleshoot, and resolve performance issues in production.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Causes of slow queries
- Performance troubleshooting workflow
- Query vs Scan performance
- Large partition problems
- Large item impact
- GSI performance
- Pagination
- CloudWatch metrics
- Production optimization strategies

---

# Performance Architecture

```text
Application

      │

      ▼

API Layer

      │

      ▼

Amazon DynamoDB

      │

      ▼

Storage Partitions
```

Application latency is often influenced by every layer, not just DynamoDB.

---

# Expected Performance

Well-designed tables typically achieve:

```text
Query

↓

Single-digit ms
```

Poorly designed tables may experience:

```text
Query

↓

Hundreds of ms

↓

Seconds
```

---

# Common Causes

Most performance problems originate from:

- Scan operations
- Poor access patterns
- Large items
- Large partitions
- Missing GSIs
- Excessive retries
- Network latency
- Application bottlenecks

---

# Investigation Workflow

```text
Slow API

      │

      ▼

Application Logs

      │

      ▼

CloudWatch Metrics

      │

      ▼

Identify Query Pattern

      │

      ▼

Optimize
```

---

# Scan vs Query

Poor:

```text
API

↓

Scan

↓

Entire Table
```

Better:

```text
API

↓

Query

↓

Single Partition
```

---

# Example

Table:

```text
Orders

20 Million Items
```

Bad API:

```text
GET /orders

↓

Scan Entire Table
```

Better:

```text
GET /customers/C100/orders

↓

Query

↓

Matching Partition
```

---

# Missing Access Pattern

Suppose an application needs:

```text
Find Orders

↓

By Status
```

Without a GSI:

```text
Scan

↓

Slow
```

With a GSI:

```text
Query

↓

Fast
```

---

# Large Partitions

One customer:

```text
50 Million Orders
```

Partition:

```text
Huge

↓

Slower Queries

↓

Pagination
```

Large partitions increase the amount of data DynamoDB must evaluate for each request.

---

# Large Items

Example:

```text
Item

↓

400 KB
```

Compared to:

```text
Item

↓

2 KB
```

Large items:

- Increase latency
- Consume more capacity
- Increase network traffic

---

# Better Design

Instead of:

```text
Order

↓

Images

↓

Documents

↓

Logs

↓

Everything
```

Store:

```text
Order Metadata

↓

S3

↓

Large Files
```

---

# Inefficient Projection

Bad:

```text
Return Entire Item
```

Good:

```text
ProjectionExpression

↓

Only Required Attributes
```

---

# Query Pagination

Maximum response:

```text
1 MB
```

Workflow:

```text
Query

↓

Page 1

↓

LastEvaluatedKey

↓

Page 2
```

Ignoring pagination leads to incomplete results.

---

# Client-Side Bottlenecks

Sometimes DynamoDB is healthy.

Problem:

```text
Application

↓

JSON Parsing

↓

Serialization

↓

Slow Response
```

Always measure:

- Database latency
- Network latency
- Application latency

---

# Network Latency

Cloud architecture:

```text
EC2

↓

Same Region

↓

Low Latency
```

Poor architecture:

```text
Client

↓

Different Continent

↓

Higher Network Delay
```

---

# CloudWatch Metrics

Monitor:

```text
SuccessfulRequestLatency

ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ReadThrottleEvents

WriteThrottleEvents
```

---

# CLI Investigation

Describe table:

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Review:

- Billing mode
- Capacity
- GSIs
- Table size

---

# Using Projection Expressions

Instead of:

```text
Customer Record

↓

Entire Object
```

Use:

```text
Customer Name

Customer Status
```

Only fetch required attributes.

---

# Avoid Filtering Large Result Sets

Poor:

```text
Query

↓

100,000 Items

↓

Filter

↓

10 Items
```

Better:

```text
Partition Key

↓

10 Items

↓

Return
```

Filtering happens **after** reading.

---

# GSI Optimization

Without GSI:

```text
Query Impossible

↓

Scan
```

With GSI:

```text
Query

↓

Fast
```

---

# Batch Operations

Poor:

```text
100 Individual Reads
```

Better:

```text
BatchGetItem
```

Reduces network round trips.

---

# Caching

Frequently accessed data:

```text
Application

↓

Redis / DAX

↓

Cache Hit

↓

No DynamoDB Request
```

Benefits:

- Lower latency
- Reduced read capacity consumption

---

# DAX

Ideal for:

- Product catalog
- User profile
- Configuration
- Session data

Architecture:

```text
Application

↓

DAX

↓

DynamoDB
```

---

# Production Performance Workflow

```text
Slow API

↓

CloudWatch

↓

Application Logs

↓

Identify Query

↓

Review Access Pattern

↓

Optimize Schema

↓

Deploy
```

---

# Performance Checklist

Investigate:

- Query vs Scan
- Item size
- GSI usage
- Partition key
- Hot partitions
- Throttling
- Pagination
- Network latency
- Application code

---

# Optimization Strategies

- Replace Scan with Query.
- Design proper GSIs.
- Reduce item size.
- Cache frequently accessed data.
- Retrieve only required attributes.
- Batch requests.
- Avoid unnecessary strong consistency.
- Keep related compute in the same AWS Region.

---

# Production Architecture

```text
Client

      │

      ▼

Load Balancer

      │

      ▼

Backend Service

      │

      ▼

Redis / DAX

      │

      ▼

Amazon DynamoDB

      │

      ▼

CloudWatch
```

---

# Performance Considerations

- Single-digit millisecond latency requires proper table design.
- Large items consume more read capacity.
- Projection Expressions reduce network traffic.
- Queries scale better than Scans.
- Caching significantly reduces read pressure.
- Monitor latency continuously.

---

# Best Practices

- Design around access patterns.
- Avoid Scan in production APIs.
- Use GSIs for alternate query paths.
- Keep items small.
- Store large files in Amazon S3.
- Use Batch APIs when appropriate.
- Monitor latency with CloudWatch.

---

# Common Mistakes

## Assuming DynamoDB Is Always Fast

Performance depends on:

- Schema
- Queries
- Item size
- Access patterns

---

## Returning Entire Items

Large responses increase:

- Network time
- Serialization time
- Application latency

---

## Using Scan for Search

Searching via Scan does not scale.

Model the data for Query instead.

---

## Ignoring Application Latency

Sometimes the database responds in:

```text
5 ms
```

while the application spends:

```text
300 ms

↓

Serialization

↓

Business Logic

↓

Response
```

Measure every layer.

---

# Interview Notes

### Why can a DynamoDB query become slow?

Common reasons include poor partition-key design, use of Scan instead of Query, missing GSIs, large item sizes, hot partitions, excessive retries, or application-side processing overhead.

---

### Does DynamoDB latency increase as the table grows?

Not necessarily. Query performance depends on the partition being accessed rather than the total table size. However, poorly designed access patterns and oversized partitions can increase latency.

---

### Why are Projection Expressions important?

Projection Expressions return only the required attributes, reducing network traffic, serialization overhead, and read capacity consumption.

---

### Why should large files be stored in Amazon S3 instead of DynamoDB?

DynamoDB is optimized for low-latency structured data. Storing large binary objects increases item size, latency, and cost. Amazon S3 is designed for durable and cost-effective object storage.

---

### How would you troubleshoot a slow DynamoDB API?

1. Measure end-to-end latency.
2. Check CloudWatch metrics.
3. Verify whether Query or Scan is used.
4. Review partition-key design and GSI usage.
5. Examine item sizes and pagination.
6. Investigate application processing and network latency.

---

# Key Takeaways

- DynamoDB can consistently deliver single-digit millisecond latency when tables are designed around access patterns.
- Most performance problems originate from application design rather than the database service itself.
- Queries, efficient partition keys, GSIs, Projection Expressions, and caching are fundamental optimization techniques.
- Always investigate the complete request path—from client to database—before concluding that DynamoDB is the bottleneck.
- Performance tuning is an ongoing process that combines good schema design, monitoring, and production benchmarking.