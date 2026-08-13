# 13 - Production Best Practices

## Overview

Secondary indexes are one of the most powerful features in DynamoDB, but they are also one of the easiest ways to create expensive, slow, and difficult-to-maintain systems.

Production-grade DynamoDB deployments do not simply "add indexes."

Instead, they follow a disciplined design process that balances:

- Performance
- Scalability
- Availability
- Operational simplicity
- Cost efficiency
- Future maintainability

This chapter summarizes the best practices used by experienced backend engineers when designing and operating DynamoDB indexes at scale.

---

# Design Around Access Patterns

The most important DynamoDB principle is:

> **Design indexes for application queries—not for your data model.**

Traditional SQL databases are often designed like this:

```text
Tables

↓

Relationships

↓

Indexes
```

DynamoDB reverses the process.

```text
Business Requirements

↓

Application Queries

↓

Primary Key

↓

Secondary Indexes
```

Every index should exist because it answers a specific business question.

---

# Start with the Primary Key

Before creating any secondary index, maximize what can be achieved using the primary key.

Example:

```text
PK = CustomerID

SK = OrderDate
```

Supports:

- Latest orders
- Order history
- Orders between dates
- Pagination
- Chronological sorting

A well-designed primary key often eliminates the need for additional indexes.

---

# Keep the Number of GSIs Small

Every additional GSI increases:

- Storage
- Write amplification
- Replication
- Monitoring
- Operational cost

Instead of:

```text
10 Small GSIs
```

Prefer:

```text
2-4 Well Designed GSIs
```

that support multiple access patterns.

---

# Design High-Cardinality Partition Keys

Good Partition Keys distribute traffic evenly.

Examples:

```text
UserID

CustomerID

OrderID

InvoiceID

DeviceID
```

Avoid:

```text
Country

Status

Region

Department

Role
```

unless combined with another attribute.

Example:

```text
Status#Region

Status#Date

Country#Month
```

---

# Build Composite Sort Keys

Sort Keys should support:

- Ordering
- Filtering
- Hierarchies
- Multiple business queries

Instead of:

```text
Timestamp
```

Prefer:

```text
Priority#Timestamp
```

or

```text
Department#Role#EmployeeID
```

Composite Sort Keys maximize index reuse.

---

# Use Sparse Indexes Whenever Possible

If only a subset of records needs to be queried,

don't index everything.

Example:

Instead of:

```text
All Orders
```

Index only:

```text
Pending Orders
```

Benefits:

- Smaller index
- Lower storage
- Lower write cost
- Faster queries

---

# Choose Projection Types Carefully

Never default to:

```text
ALL
```

Choose the smallest projection that satisfies the application.

Decision guide:

```text
KEYS_ONLY

↓

Minimal Storage
```

```text
INCLUDE

↓

Most Production Workloads
```

```text
ALL

↓

Only When Necessary
```

---

# Avoid Scan Operations

If an application requires:

```text
Scan

↓

Filter

↓

Return Results
```

the schema should be reconsidered.

Production applications should primarily use:

```text
Query
```

supported by appropriate indexes.

---

# Reuse Indexes

Before creating a new index, ask:

```text
Can an Existing Index

Support This Query?
```

Often,

a composite Sort Key enables several related access patterns using one index.

Fewer indexes mean:

- Lower cost
- Simpler maintenance
- Better scalability

---

# Design for Future Growth

Applications evolve.

Instead of designing only for today's requirements,

anticipate reasonable future queries.

Example:

Rather than:

```text
PK = CustomerID
```

Prefer:

```text
PK = CustomerID

SK = OrderDate
```

This accommodates future reporting, sorting, and time-based queries without major redesign.

---

# Expect Eventual Consistency

Remember:

```text
GSIs

↓

Eventually Consistent
```

Applications should:

- Retry if necessary
- Avoid critical read-after-write workflows using GSIs
- Read from the base table when immediate consistency is required

---

# Optimize for Write Amplification

Every write updates:

```text
Base Table

+

Every Matching GSI
```

Estimate write amplification before introducing a new index.

For write-heavy systems:

- Keep projections small
- Minimize the number of GSIs
- Prefer Sparse Indexes

---

# Monitor Continuously

Production systems should continuously monitor index health.

Important CloudWatch metrics:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- SuccessfulRequestLatency
- ThrottledRequests
- OnlineIndexThrottleEvents
- Storage utilization

Monitoring identifies:

- Hot partitions
- Unused indexes
- Capacity bottlenecks
- Cost optimization opportunities

---

# Review Indexes Periodically

Indexes created years ago may no longer be useful.

A quarterly review should answer:

- Is this index still queried?
- Can two indexes be merged?
- Can projection be reduced?
- Is a Sparse Index more appropriate?
- Is traffic evenly distributed?

Treat indexes as evolving infrastructure.

---

# Load Test Before Production

Do not assume an index performs well because it works in development.

Simulate production workloads.

Test:

- Millions of records
- Concurrent users
- Peak traffic
- Batch writes
- Range queries
- Pagination

Validate:

- Latency
- Throughput
- Throttling
- Cost

---

# Real-World Example — E-commerce

Requirements:

```text
Customer Orders

↓

Pending Orders

↓

Latest Orders

↓

Monthly Reports
```

Indexes:

```text
CustomerDateGSI
```

```text
PendingSparseGSI
```

Analytics handled separately.

Instead of creating many specialized indexes,

two carefully designed GSIs satisfy multiple business requirements.

---

# Real-World Example — SaaS Platform

Tenant data:

```text
PK = TenantID

SK = ResourceID
```

Additional index:

```text
TenantActivityGSI

PK = TenantID

SK = LastModified
```

Supports:

- Latest resources
- Recent updates
- Activity dashboard

One index powers several features.

---

# Production Checklist

Before deploying a new index, verify:

- Supports a real business query
- High-cardinality Partition Key
- Meaningful Sort Key
- Minimal projection
- Query instead of Scan
- Write amplification estimated
- Supports multiple access patterns
- Monitoring configured
- Load tested
- Documented for future engineers

---

# Operational Lifecycle

```text
Business Requirement

↓

Design Access Pattern

↓

Create Index

↓

Load Testing

↓

Production Deployment

↓

CloudWatch Monitoring

↓

Performance Review

↓

Optimization

↓

Repeat
```

Index management is an ongoing engineering process rather than a one-time activity.

---

# Enterprise Architecture

```text
                     Application

                           │

                Business Requirements

                           │

                           ▼

                 Access Pattern Analysis

                           │

                           ▼

               Primary Key Optimization

                           │

                           ▼

              Secondary Index Design

                           │

                           ▼

                Load Testing & Validation

                           │

                           ▼

                 Production Deployment

                           │

                           ▼

                 CloudWatch Monitoring

                           │

                           ▼

              Continuous Optimization
```

Successful DynamoDB systems evolve continuously as workloads change.

---

# Best Practices Summary

| Area | Recommendation |
|------|----------------|
| Index Creation | Only for real access patterns |
| Partition Key | High-cardinality values |
| Sort Key | Composite and business-oriented |
| Projection | Prefer INCLUDE |
| Queries | Always prefer Query over Scan |
| GSIs | Keep the number minimal |
| Sparse Indexes | Use whenever practical |
| Monitoring | Review CloudWatch metrics continuously |
| Performance | Load test before production |
| Maintenance | Review and optimize indexes regularly |

---

# Common Production Mistakes

## Creating Indexes Too Early

Avoid creating indexes for hypothetical future features.

Build indexes only when real business requirements exist.

---

## Ignoring Cost

Indexes improve performance but increase storage and write costs.

Always estimate operational expense.

---

## Overlooking Monitoring

An unhealthy index may not become obvious until traffic increases.

Continuous monitoring prevents production incidents.

---

## Forgetting Documentation

Every index should have documented:

- Business purpose
- Access pattern
- Owner
- Projection type
- Capacity considerations

Good documentation simplifies long-term maintenance.

---

# Interview Notes

A common interview question is:

> **What are the most important best practices for DynamoDB indexes?**

Design around access patterns, use high-cardinality Partition Keys, minimize GSIs, choose appropriate projection types, monitor CloudWatch metrics, avoid scans, and periodically review index usage.

Another common question is:

> **How do large organizations manage DynamoDB indexes?**

Through continuous monitoring, performance testing, quarterly architecture reviews, cost optimization, and documenting the business purpose of every index.

Another common question is:

> **Why is documentation important for secondary indexes?**

Without documentation, future engineers may not understand why an index exists, leading to accidental deletion, duplicate indexes, or unnecessary operational costs.

---

# Key Takeaways

- Production-grade index design begins with business access patterns rather than database structure.
- A small number of well-designed indexes is usually better than many specialized indexes.
- High-cardinality Partition Keys, composite Sort Keys, and minimal projections maximize scalability.
- Continuous monitoring, load testing, and periodic reviews keep indexes performant and cost-efficient.
- Indexes are operational assets that require ongoing optimization throughout the lifecycle of an application.
- Well-designed indexes enable DynamoDB to deliver predictable, low-latency performance at massive scale.