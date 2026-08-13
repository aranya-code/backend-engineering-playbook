# 11 - Performance Optimization

## Overview

One of the biggest advantages of Amazon DynamoDB is its ability to deliver **single-digit millisecond latency** at virtually any scale.

However, this level of performance does **not happen automatically**.

Poor table design, inefficient queries, hot partitions, unnecessary scans, oversized items, and incorrect capacity settings can quickly degrade performance and dramatically increase costs.

Performance optimization is not about writing faster Python code—it's about **designing the database and access patterns correctly**.

This chapter covers the techniques senior backend engineers use to optimize DynamoDB applications in production.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What affects DynamoDB performance
- Read and write capacity optimization
- Hot partitions
- Partition key design
- Efficient querying
- Item size optimization
- Batch operations
- Caching
- Adaptive Capacity
- Auto Scaling
- Monitoring performance
- Production best practices
- Interview questions

---

# Performance Architecture

```text
                Client

                   │

                   ▼

              API Gateway

                   │

                   ▼

              FastAPI API

                   │

                   ▼

         Repository Layer

                   │

                   ▼

      Efficient Query Design

                   │

                   ▼

         Well Distributed Keys

                   │

                   ▼

             Amazon DynamoDB
```

Performance starts with the data model.

---

# Factors Affecting Performance

The biggest performance factors are:

- Table design
- Partition key selection
- Query patterns
- Item size
- Capacity mode
- Secondary indexes
- Network latency
- Retry behavior

Most production performance issues originate from poor data modeling.

---

# Query vs Scan

Preferred:

```text
Query

↓

Target Partition

↓

Fast
```

Avoid:

```text
Scan

↓

Entire Table

↓

Slow
```

A single Scan can consume thousands of RCUs.

---

# Design for Access Patterns

Never design the table first.

Instead:

```text
Business Questions

↓

Access Patterns

↓

Partition Key

↓

Sort Key

↓

Indexes

↓

Table Design
```

This is the fundamental DynamoDB design philosophy.

---

# Choose a Good Partition Key

A partition key should distribute requests evenly.

Good:

```text
customer_id

order_id

invoice_id
```

Poor:

```text
country

status

active
```

Poor partition keys create hot partitions.

---

# Hot Partitions

Imagine:

```text
Partition A

95% Traffic

──────────────

Partition B

2%

──────────────

Partition C

3%
```

Partition A becomes overloaded while others remain idle.

---

# Even Distribution

Preferred:

```text
Partition A

33%

──────────────

Partition B

34%

──────────────

Partition C

33%
```

Balanced traffic maximizes throughput.

---

# High Cardinality Keys

High-cardinality attributes make better partition keys.

Examples:

```text
UUID

Customer ID

Order ID

User ID
```

Avoid attributes with very few distinct values.

---

# Keep Items Small

Larger items require:

- More storage
- More network bandwidth
- Higher read cost
- Higher write cost

Poor:

```text
350 KB Item
```

Better:

```text
2 KB Item
```

Store only what the application needs.

---

# ProjectionExpression

Instead of retrieving:

```text
Entire Item
```

Retrieve only:

```text
Name

Status

Amount
```

Example:

```python
response = table.query(
    KeyConditionExpression=...,
    ProjectionExpression=
        "customer_name,status"
)
```

Smaller responses reduce latency.

---

# Use Batch Operations

Poor:

```text
500 GetItem Requests
```

Better:

```text
BatchGetItem
```

Likewise:

```text
500 PutItem Requests
```

Better:

```text
batch_writer()
```

Fewer network calls improve performance.

---

# Avoid Unnecessary Strong Consistency

Eventually consistent reads:

```text
Lower Cost

Higher Throughput
```

Strongly consistent reads:

```text
Higher Cost

Lower Throughput
```

Use strong consistency only when the latest committed data is required immediately.

---

# Optimize Secondary Indexes

Every index:

- Consumes storage
- Increases write cost
- Requires maintenance

Create indexes only for real access patterns.

Unused GSIs increase costs without providing value.

---

# Adaptive Capacity

DynamoDB automatically redistributes capacity to busy partitions.

```text
Hot Partition

↓

Adaptive Capacity

↓

Additional Resources
```

Adaptive Capacity helps absorb uneven workloads but should not be relied upon to compensate for poor partition key design.

---

# On-Demand vs Provisioned Capacity

| Feature | On-Demand | Provisioned |
|----------|-----------|-------------|
| Traffic Pattern | Unpredictable | Predictable |
| Auto Scaling | Automatic | Configurable |
| Management | Minimal | More Control |
| Cost | Higher at Scale | Lower if Well Planned |

Choose the capacity mode based on workload characteristics.

---

# Auto Scaling

Provisioned tables can automatically adjust throughput.

```text
Traffic Increases

↓

CloudWatch Alarm

↓

Auto Scaling

↓

Higher Capacity
```

This helps avoid throttling during predictable growth.

---

# DAX (DynamoDB Accelerator)

DAX is an in-memory cache for DynamoDB.

```text
Application

↓

DAX

↓

Cache Hit

↓

Return Result
```

Cache miss:

```text
Application

↓

DAX

↓

DynamoDB

↓

Store in Cache
```

DAX is particularly effective for read-heavy workloads.

---

# Application-Level Caching

Another option:

```text
Application

↓

Redis

↓

Cache Hit

↓

Return

↓

Cache Miss

↓

DynamoDB
```

Many production systems combine Redis with DynamoDB.

---

# Parallel Scans

Large administrative jobs may benefit from:

```text
Worker 1

Worker 2

Worker 3

Worker N
```

Each worker scans a different segment.

Use parallel scans only for offline processing or maintenance tasks.

---

# Reduce Network Calls

Poor:

```text
Application

↓

1 Request

↓

Repeat 1,000 Times
```

Better:

```text
Batch Requests

↓

Fewer Round Trips
```

---

# Pagination

Never load millions of records into memory.

Preferred:

```text
Read Page

↓

Process

↓

Read Next Page
```

This keeps memory usage predictable.

---

# Retry Strategy

Use:

```text
Retry

↓

Exponential Backoff

↓

Jitter
```

Avoid retry storms during throttling events.

---

# CloudWatch Metrics

Monitor:

- SuccessfulRequestLatency
- ThrottledRequests
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- SystemErrors
- UserErrors

These metrics provide early indicators of scaling or design problems.

---

# Performance Troubleshooting Flow

```text
High Latency

↓

Query or Scan?

↓

Scan

↓

Replace with Query

────────────

Query

↓

Hot Partition?

↓

Improve Partition Key

────────────

Still Slow?

↓

Check Capacity

↓

Monitor CloudWatch
```

---

# Repository Pattern

```python
class OrderRepository:

    def get_orders(
        self,
        customer_id
    ):

        return self.table.query(
            KeyConditionExpression=...
        )
```

Repository classes make it easier to optimize database access without affecting business logic.

---

# Production Architecture

```text
            Client

               │

               ▼

          FastAPI API

               │

               ▼

        Repository Layer

               │

               ▼

     Query + Projection

               │

               ▼

         Redis / DAX

               │

               ▼

        Amazon DynamoDB
```

---

# Performance Optimization Checklist

Before deploying:

✓ Query instead of Scan

✓ High-cardinality partition keys

✓ Efficient GSIs

✓ ProjectionExpression

✓ Pagination

✓ Batch operations

✓ Auto Scaling

✓ Monitoring

✓ Retry strategy

✓ Caching

---

# Security Considerations

Performance optimizations should never bypass security controls.

Continue to:

- Apply least-privilege IAM policies
- Encrypt data with AWS KMS
- Audit API activity with CloudTrail
- Protect cached sensitive data
- Monitor abnormal traffic patterns

---

# Best Practices

- Design around access patterns.
- Prefer Query over Scan.
- Choose high-cardinality partition keys.
- Keep items small.
- Use ProjectionExpression.
- Batch reads and writes where appropriate.
- Cache frequently accessed data.
- Monitor CloudWatch metrics continuously.
- Enable Auto Scaling for provisioned tables.
- Review unused GSIs periodically.

---

# Common Mistakes

## Using Scan for Production APIs

Poor:

```python
table.scan()
```

Better:

```python
table.query(...)
```

---

## Choosing Low-Cardinality Partition Keys

Example:

```text
status

country

department
```

These can create hot partitions and uneven traffic distribution.

---

## Overusing Strongly Consistent Reads

Use them only when absolutely necessary.

Most workloads perform well with eventually consistent reads.

---

## Returning Entire Items

Avoid transferring attributes that the client doesn't need.

Use:

```python
ProjectionExpression
```

---

## Ignoring Monitoring

Performance problems are often detected first through CloudWatch metrics.

Continuous monitoring is essential.

---

# Interview Notes

A common interview question is:

> **What causes poor DynamoDB performance?**

Common causes include table scans, hot partitions, low-cardinality partition keys, oversized items, excessive strongly consistent reads, and poorly designed secondary indexes.

---

Another common question is:

> **How do you prevent hot partitions?**

Choose high-cardinality partition keys that distribute requests evenly across partitions, avoiding attributes with very few unique values.

---

Another common question is:

> **When would you use DynamoDB Accelerator (DAX)?**

DAX is appropriate for read-heavy workloads with frequently accessed data where microsecond-level read latency is beneficial.

---

Another common question is:

> **What metrics would you monitor to optimize DynamoDB performance?**

Monitor request latency, throttled requests, consumed read/write capacity units, system errors, user errors, and Auto Scaling activity through Amazon CloudWatch.

---

# Key Takeaways

- DynamoDB performance depends primarily on **good data modeling**, not query optimization after deployment.
- Design tables around access patterns and use high-cardinality partition keys to distribute traffic evenly.
- Prefer `Query` over `Scan`, keep items small, and retrieve only required attributes with `ProjectionExpression`.
- Use batch operations, pagination, caching (Redis or DAX), and Auto Scaling to improve scalability.
- Continuously monitor CloudWatch metrics to detect hot partitions, throttling, and latency issues before they impact production.