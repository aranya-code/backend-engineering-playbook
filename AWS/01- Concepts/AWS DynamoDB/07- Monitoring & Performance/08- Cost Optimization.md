# 08 - Cost Optimization

## Overview

Amazon DynamoDB is designed to scale from a few requests per second to millions of requests per second without infrastructure management. However, this scalability comes with the responsibility of controlling operational costs.

Many organizations spend significantly more than necessary because of:

- Poor table design
- Over-provisioned capacity
- Inefficient access patterns
- Unused indexes
- Large item sizes
- Expensive Scan operations

Cost optimization in DynamoDB is **not about making the database cheaper**—it's about maximizing performance while minimizing unnecessary resource consumption.

This chapter covers the techniques used by experienced backend engineers and cloud architects to optimize DynamoDB costs in production.

---

# Learning Objectives

After completing this chapter, you'll understand:

- DynamoDB pricing fundamentals
- Capacity cost optimization
- Storage optimization
- Index optimization
- Read optimization
- Write optimization
- Monitoring costs
- Cost optimization strategies
- Production recommendations
- Interview questions

---

# DynamoDB Pricing Components

DynamoDB charges for several resources.

```text
                 DynamoDB Cost

                      │

      ┌───────────────┼───────────────┐

      ▼               ▼               ▼

 Capacity        Storage        Features

      │               │               │

      ▼               ▼               ▼

RCUs/WCUs       GB Stored     Streams, Backup,
                               Global Tables,
                               DAX, etc.
```

Understanding where money is spent is the first step toward optimization.

---

# Major Cost Drivers

The primary contributors to DynamoDB costs are:

- Read Capacity
- Write Capacity
- Data Storage
- Global Secondary Indexes
- Backups
- Point-in-Time Recovery (PITR)
- Global Tables
- DynamoDB Streams

---

# Choose the Right Capacity Mode

One of the biggest cost decisions is selecting the appropriate capacity mode.

### Provisioned Mode

Best for:

- Predictable workloads
- Stable traffic
- Long-running enterprise systems

```text
Stable Traffic

↓

Provisioned Capacity

↓

Lower Cost
```

---

### On-Demand Mode

Best for:

- Unknown workloads
- Spiky traffic
- New applications

```text
Unpredictable Traffic

↓

On-Demand

↓

Pay Per Request
```

---

# Avoid Over-Provisioning

Poor example:

```text
Provisioned

↓

10,000 RCUs

Actual Usage

↓

800 RCUs
```

Most of the allocated capacity is wasted.

Better approach:

```text
Provisioned

↓

1,000 RCUs

Auto Scaling

↓

Increase When Needed
```

---

# Enable Auto Scaling

Auto Scaling helps avoid paying for unused capacity.

```text
Traffic Increases

↓

CloudWatch

↓

Auto Scaling

↓

Increase Capacity

↓

Traffic Drops

↓

Reduce Capacity
```

This balances performance and cost.

---

# Optimize Read Costs

Reads consume RCUs.

Reduce costs by:

- Using eventually consistent reads
- Caching frequently accessed data
- Query instead of Scan
- Reading only required attributes

---

# Eventually Consistent Reads

Eventually consistent reads consume approximately half the read capacity of strongly consistent reads.

```text
Strong Read

↓

Higher Cost

────────────

Eventually Consistent

↓

Lower Cost
```

Use eventual consistency whenever business requirements allow.

---

# Use Projection Expressions

Poor:

```text
Retrieve Entire Item

↓

40 KB
```

Better:

```text
Retrieve

↓

Name

Email

Status
```

Benefits:

- Lower network transfer
- Smaller responses
- Faster APIs

---

# Query Instead of Scan

Poor workflow:

```text
Scan

↓

Entire Table

↓

High Cost
```

Better:

```text
Query

↓

Partition Key

↓

Minimal Capacity
```

Query operations are significantly more efficient.

---

# Reduce Item Size

Smaller items reduce:

- Storage costs
- RCU consumption
- WCU consumption

Example:

```text
Customer Item

↓

60 KB

↓

Optimized

↓

5 KB
```

---

# Store Large Objects in Amazon S3

Avoid storing:

- Images
- Videos
- PDFs
- Documents

Instead:

```text
Amazon S3

↓

Object URL

↓

Stored in DynamoDB
```

This reduces both storage costs and capacity consumption.

---

# Optimize Write Costs

Writes consume WCUs.

Reduce unnecessary writes by:

- Updating only changed attributes
- Eliminating duplicate writes
- Using conditional updates
- Reducing unnecessary indexes

---

# Remove Unused GSIs

Every write updates:

- Base table
- Every Global Secondary Index

```text
Write

↓

Table

↓

GSI 1

↓

GSI 2

↓

GSI 3
```

Unused indexes increase both storage and write costs.

---

# Archive Old Data

Historical records often receive little or no traffic.

Move infrequently accessed data to:

- Amazon S3
- Amazon Glacier
- Data Lake

Example:

```text
Orders

↓

Older Than 2 Years

↓

Archive

↓

S3
```

---

# Use Time-to-Live (TTL)

Expired data consumes storage until removed.

Example:

```text
Session

↓

Expires

↓

TTL

↓

Automatic Deletion
```

Benefits:

- Lower storage costs
- Smaller tables
- Better performance

---

# Monitor Cost with CloudWatch

Track:

```text
Consumed RCUs

Consumed WCUs

Provisioned RCUs

Provisioned WCUs

Storage Usage
```

Unexpected growth may indicate:

- Traffic spikes
- Bugs
- Inefficient queries

---

# Monitor AWS Cost Explorer

CloudWatch shows resource usage.

AWS Cost Explorer shows billing trends.

```text
CloudWatch

↓

Operational Metrics

────────────

Cost Explorer

↓

Financial Metrics
```

Use both together for complete visibility.

---

# Optimize Backup Costs

Backups are essential but consume storage.

Best practices:

- Delete obsolete backups
- Define retention policies
- Automate lifecycle management

---

# Evaluate Global Tables Carefully

Global Tables provide:

- Multi-region replication
- Low-latency access
- Disaster recovery

However, every write is replicated across regions.

```text
Write

↓

Region A

↓

Region B

↓

Region C
```

More regions increase operational costs.

---

# Cost Optimization Workflow

```text
Analyze Usage

↓

Identify Waste

↓

Optimize Capacity

↓

Optimize Queries

↓

Optimize Storage

↓

Monitor

↓

Repeat
```

Cost optimization is a continuous process.

---

# Cost Optimization Checklist

Before production verify:

- Appropriate capacity mode selected
- Auto Scaling enabled
- Query used instead of Scan
- Eventual consistency evaluated
- Large objects stored in S3
- TTL configured
- Unused GSIs removed
- Backups reviewed
- CloudWatch monitoring enabled
- Cost Explorer reviewed monthly

---

# Production Architecture

```text
                 Application

                      │

                      ▼

               DynamoDB Table

          ┌───────────┼───────────┐

          ▼           ▼           ▼

     Auto Scaling   CloudWatch   TTL

          │           │           │

          ▼           ▼           ▼

     Capacity     Monitoring   Cleanup

          │

          ▼

   Lower Operational Cost
```

---

# Best Practices

- Select the correct capacity mode.
- Enable Auto Scaling for provisioned tables.
- Prefer Query over Scan.
- Use eventually consistent reads whenever possible.
- Keep items small.
- Store large files in Amazon S3.
- Remove unused GSIs.
- Configure TTL for temporary data.
- Review Cost Explorer regularly.
- Continuously monitor CloudWatch metrics.

---

# Common Mistakes

## Over-Provisioning Capacity

Allocating significantly more RCUs or WCUs than required increases costs without improving performance.

---

## Using Scan for Everything

Scans consume unnecessary capacity and increase both cost and latency.

---

## Keeping Expired Data Forever

Old sessions, logs, and temporary records continue consuming storage until deleted.

TTL automates this cleanup.

---

## Creating Excessive GSIs

Every additional GSI increases:

- Storage
- Write cost
- Maintenance overhead

Create indexes only for required access patterns.

---

## Ignoring Cost Monitoring

Unexpected cost increases often reveal:

- Application bugs
- Traffic anomalies
- Poor query design
- Capacity misconfiguration

Regular monitoring prevents surprises.

---

# Production Considerations

Large organizations typically combine:

```text
CloudWatch

↓

AWS Cost Explorer

↓

AWS Budgets

↓

AWS Trusted Advisor

↓

AWS Organizations

↓

Cost Allocation Tags
```

This enables:

- Budget tracking
- Department-level chargeback
- Resource optimization
- Cost forecasting
- Financial governance

---

# Interview Notes

A common interview question is:

> **How do you reduce DynamoDB costs?**

Optimize capacity mode, enable Auto Scaling, use Query instead of Scan, reduce item size, remove unused GSIs, enable TTL, use eventually consistent reads where possible, and monitor costs continuously.

---

Another common question is:

> **Why are Scan operations expensive?**

Scan reads every item in a table or partition, consuming significantly more RCUs than Query operations, which read only matching items.

---

Another common question is:

> **How does TTL help reduce costs?**

TTL automatically removes expired items, reducing storage costs and improving overall table efficiency without requiring manual cleanup jobs.

---

Another common question is:

> **What is the biggest hidden cost in DynamoDB?**

Poor schema design often leads to inefficient access patterns, unnecessary scans, oversized items, and excessive GSIs—all of which increase both performance overhead and operational costs.

---

# Key Takeaways

- Cost optimization begins with good data modeling and efficient access patterns.
- Choose the appropriate capacity mode based on workload characteristics.
- Use Query instead of Scan and eventually consistent reads whenever possible.
- Keep items small and store large objects in Amazon S3.
- Remove unused GSIs and configure TTL for temporary data.
- Continuously monitor operational metrics and billing trends to maintain cost-efficient production workloads.