# 07 - Performance Troubleshooting

## Overview

No matter how well a DynamoDB table is designed, production systems eventually experience performance issues.

These issues may include:

- Increased latency
- Read throttling
- Write throttling
- Hot partitions
- Capacity exhaustion
- Expensive scans
- Slow application response times

The goal of troubleshooting is **not just fixing the immediate problem**, but identifying and eliminating the root cause.

This chapter provides a systematic approach used by senior backend engineers to diagnose and resolve DynamoDB performance issues in production.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Common DynamoDB performance issues
- A structured troubleshooting methodology
- Diagnosing throttling
- Diagnosing latency
- Capacity troubleshooting
- Hot partition investigation
- CloudWatch metrics for troubleshooting
- Production debugging workflow
- Best practices
- Interview questions

---

# Performance Troubleshooting Workflow

```text
Performance Issue

        │

        ▼

Identify Symptoms

        │

        ▼

Collect Metrics

        │

        ▼

Identify Root Cause

        │

        ▼

Apply Fix

        │

        ▼

Validate Improvement
```

Never begin by randomly increasing capacity.

---

# Common Performance Problems

| Problem | Typical Symptoms |
|----------|------------------|
| Read throttling | Failed reads, retries |
| Write throttling | Failed writes |
| High latency | Slow API responses |
| Hot partitions | Uneven throughput |
| Expensive scans | High RCU usage |
| Capacity exhaustion | Frequent throttling |
| Inefficient indexes | Slow queries |
| Large items | High latency and cost |

---

# Step 1 — Identify the Symptoms

Ask questions such as:

- Is latency increasing?
- Are requests failing?
- Is throttling occurring?
- Did traffic recently increase?
- Did a deployment occur?
- Is only one API affected?

Example:

```text
Customer Reports

↓

Slow Checkout API

↓

Investigate Orders Table
```

---

# Step 2 — Check CloudWatch

Review:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ReadThrottleEvents

WriteThrottleEvents

SuccessfulRequestLatency

SystemErrors

UserErrors
```

CloudWatch is usually the starting point.

---

# Problem 1 — Read Throttling

Symptoms:

```text
GetItem

↓

Provisioned Limit Reached

↓

ReadThrottleEvents

↓

Retries
```

Possible causes:

- Insufficient RCUs
- Hot partitions
- Traffic spike
- Scan operations
- Cache failure

Solutions:

- Increase capacity
- Enable Auto Scaling
- Improve partition key
- Replace Scan with Query
- Add caching

---

# Problem 2 — Write Throttling

Workflow:

```text
PutItem

↓

Capacity Exceeded

↓

WriteThrottleEvents
```

Possible causes:

- Insufficient WCUs
- Hot partition
- Batch import
- Traffic spike
- Too many GSIs

Solutions:

- Increase WCUs
- Optimize partition keys
- Reduce unnecessary writes
- Use write sharding
- Review GSIs

---

# Problem 3 — High Latency

Symptoms:

```text
Normal

↓

5 ms

────────────

Current

↓

40 ms
```

Potential causes:

- Network latency
- Hot partitions
- Large items
- Scan operations
- Retry storms
- Application bottlenecks

Always determine whether latency originates in the application or DynamoDB.

---

# Problem 4 — Hot Partitions

Symptoms:

```text
Table Capacity

↓

40% Used

────────────

One Partition

↓

100% Busy
```

Indicators:

- Uneven traffic
- High throttling
- Low overall utilization

Solutions:

- Better partition key
- Composite key
- Write sharding
- Random suffixes

---

# Problem 5 — Scan Operations

Poor workflow:

```text
Application

↓

Scan

↓

Entire Table

↓

Filter

↓

Response
```

Problems:

- High RCU consumption
- Slow response time
- Increased cost

Preferred:

```text
Application

↓

Query

↓

Partition Key

↓

Response
```

---

# Problem 6 — Large Items

Example:

```text
Customer Item

↓

250 KB
```

Large items:

- Consume more RCUs
- Consume more WCUs
- Increase serialization time
- Increase network transfer

Solutions:

- Store blobs in S3
- Split data
- Remove unnecessary attributes

---

# Problem 7 — Capacity Exhaustion

CloudWatch:

```text
Consumed

↓

99%

↓

Provisioned

↓

100%
```

Possible solutions:

- Increase provisioned capacity
- Switch to On-Demand
- Enable Auto Scaling
- Optimize queries

---

# Problem 8 — Global Secondary Index Bottlenecks

Example:

```text
Orders Table

↓

Healthy

────────────

OrdersByStatus GSI

↓

Throttling
```

Monitor GSI metrics independently.

Possible fixes:

- Increase GSI capacity
- Optimize index usage
- Remove unused indexes

---

# Problem 9 — Excessive Retries

Workflow:

```text
Throttle

↓

Retry

↓

More Load

↓

More Throttling
```

This creates a retry storm.

Solutions:

- Exponential backoff
- Jitter
- Increase capacity
- Reduce concurrency

---

# Step 3 — Identify the Root Cause

Avoid fixing symptoms.

Example:

```text
Read Throttling

↓

Why?

↓

Hot Partition

↓

Why?

↓

Poor Partition Key

↓

Root Cause
```

Fix the partition key—not just the capacity.

---

# Step 4 — Apply the Correct Fix

Example mapping:

| Issue | Recommended Fix |
|--------|-----------------|
| Scan | Replace with Query |
| Hot partition | Better partition key |
| Large item | Move blobs to S3 |
| Capacity exhaustion | Increase capacity / Auto Scaling |
| High latency | Optimize schema and queries |
| Retry storms | Exponential backoff |

---

# Step 5 — Validate

After implementing changes:

Monitor:

```text
Latency

↓

Throttle Events

↓

Capacity

↓

Application Errors
```

Ensure performance actually improves.

---

# Production Troubleshooting Workflow

```text
Alert

↓

CloudWatch

↓

Logs

↓

Identify Issue

↓

Root Cause

↓

Fix

↓

Deploy

↓

Monitor

↓

Resolved
```

---

# Useful CloudWatch Metrics

| Metric | Purpose |
|---------|----------|
| ReadThrottleEvents | Read bottlenecks |
| WriteThrottleEvents | Write bottlenecks |
| SuccessfulRequestLatency | Performance |
| ConsumedReadCapacityUnits | Read utilization |
| ConsumedWriteCapacityUnits | Write utilization |
| UserErrors | Application issues |
| SystemErrors | AWS issues |

---

# Troubleshooting Checklist

Before changing production:

- Check CloudWatch metrics
- Review recent deployments
- Review traffic increases
- Check partition key distribution
- Review query patterns
- Review Scan usage
- Check item size
- Review GSI utilization
- Review application logs

---

# Production Example

Flash sale begins.

```text
Traffic

↓

Orders Table

↓

Write Throttling

↓

CloudWatch Alarm

↓

Engineer Investigates

↓

Hot Partition Found

↓

Write Sharding Applied

↓

Traffic Stabilized
```

---

# Best Practices

- Investigate root causes before increasing capacity.
- Replace Scan operations with Query whenever possible.
- Monitor CloudWatch continuously.
- Review partition key design regularly.
- Use Auto Scaling appropriately.
- Load test before production.
- Implement exponential backoff for retries.
- Monitor GSIs independently.

---

# Common Mistakes

## Immediately Increasing Capacity

More capacity may temporarily reduce throttling but won't fix poor data modeling or hot partitions.

---

## Ignoring Application Logs

CloudWatch shows **what** happened.

Logs often explain **why** it happened.

---

## Treating All Latency as a Database Problem

High API latency may originate from:

- Application code
- Network
- External APIs
- Serialization
- Cache failures

Always investigate the complete request path.

---

## Ignoring Retry Behavior

Aggressive retry loops can amplify production incidents.

Implement exponential backoff with jitter.

---

# Production Considerations

Enterprise troubleshooting often combines:

```text
CloudWatch

↓

CloudTrail

↓

AWS X-Ray

↓

Application Logs

↓

Distributed Tracing

↓

Incident Management
```

Root cause analysis should be documented after every major production incident to prevent recurrence.

---

# Interview Notes

A common interview question is:

> **What would you do if a DynamoDB table suddenly started throttling?**

Check CloudWatch metrics, determine whether the throttling is read or write related, review recent traffic changes, investigate partition key distribution, identify any hot partitions, and then apply the appropriate fix such as schema optimization, Auto Scaling, or capacity adjustments.

---

Another common question is:

> **How do you troubleshoot high latency in DynamoDB?**

Review `SuccessfulRequestLatency`, application logs, network latency, item size, query patterns, partition distribution, and retry behavior. Confirm whether the issue is within DynamoDB or elsewhere in the application stack.

---

Another common question is:

> **Why shouldn't you immediately increase RCUs or WCUs?**

Because throttling may be caused by hot partitions, inefficient queries, or poor partition key design. Increasing capacity treats the symptom rather than addressing the underlying issue.

---

Another common question is:

> **How do you identify a hot partition?**

Look for throttling and high latency despite relatively low overall table utilization. Analyze access patterns and partition key distribution to determine whether a small subset of keys is receiving disproportionate traffic.

---

# Key Takeaways

- Performance troubleshooting should follow a structured, metrics-driven process.
- CloudWatch metrics and application logs together provide the best visibility into production issues.
- Common performance problems include throttling, hot partitions, scans, large items, and inefficient indexes.
- Always identify the root cause before applying fixes.
- Validate improvements after implementing changes and continue monitoring to ensure long-term stability.