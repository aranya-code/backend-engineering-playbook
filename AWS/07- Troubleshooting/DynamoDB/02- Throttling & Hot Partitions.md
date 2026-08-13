# 02 - Throttling & Hot Partitions

## Overview

One of the most common production issues in Amazon DynamoDB is **throttling**.

Many engineers initially assume throttling means they simply need to increase capacity. In reality, capacity is only one possible cause. A poorly designed partition key can cause a single partition to become overloaded while the rest of the table remains idle.

Understanding how DynamoDB distributes data and traffic is essential for building scalable systems.

This chapter explores throttling, hot partitions, their causes, troubleshooting techniques, and production solutions.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What throttling is
- Why throttling occurs
- Hot partitions
- Hot keys
- Adaptive Capacity
- CloudWatch metrics
- Capacity planning
- Troubleshooting workflow
- Production mitigation strategies

---

# What is Throttling?

Throttling occurs when DynamoDB cannot process additional requests because the allocated capacity for a partition or table has been exceeded.

Instead of processing the request, DynamoDB returns an error.

Typical exception:

```text
ProvisionedThroughputExceededException
```

---

# High-Level Architecture

```text
Application

      │

      ▼

Amazon DynamoDB

      │

      ▼

Partition

      │

      ▼

Capacity Limit Reached

      │

      ▼

Request Throttled
```

---

# Why Throttling Happens

Common causes include:

- Insufficient provisioned capacity
- Hot partition
- Hot partition key
- Traffic spikes
- Large batch operations
- Poor data model
- Uneven workload distribution

---

# Example

Imagine an Orders table.

Every request uses:

```text
customer_id = C100
```

Instead of:

```text
Millions of Customers
```

all traffic targets:

```text
One Partition
```

Result:

```text
Hot Partition

↓

Throttling
```

---

# Good Distribution

```text
Partition A

Orders A-M

──────────────

Partition B

Orders N-Z

──────────────

Traffic

Evenly Distributed
```

---

# Poor Distribution

```text
Partition A

99%

Traffic

──────────────

Partition B

1%

Traffic

──────────────

Hot Partition
```

---

# Hot Key

A hot key occurs when one partition key receives significantly more requests than others.

Example:

```text
Trending Product

↓

Millions of Reads

↓

Same Partition

↓

Throttle
```

---

# Hot Partition vs Hot Key

| Hot Key | Hot Partition |
|----------|---------------|
| One frequently accessed key | Entire partition overloaded |
| Often application-driven | Storage-level consequence |
| Can create hot partitions | Causes throttling |

---

# Detecting Throttling

CloudWatch metrics:

```text
ReadThrottleEvents

WriteThrottleEvents

ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

SuccessfulRequestLatency
```

These metrics should always be monitored.

---

# CLI Investigation

Describe the table.

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Review:

- Billing mode
- Capacity
- GSIs

---

# Capacity Investigation

Provisioned table:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.ProvisionedThroughput"
```

Compare:

```text
Provisioned Capacity

↓

Consumed Capacity

↓

Throttle?
```

---

# On-Demand Tables

Even On-Demand mode can throttle.

Why?

Because partitions still have physical throughput limits.

Automatic scaling is not infinite.

---

# Adaptive Capacity

DynamoDB includes Adaptive Capacity.

```text
Traffic Spike

↓

Adaptive Capacity

↓

Temporary Rebalancing
```

Benefits:

- Automatically shifts capacity
- Helps uneven workloads
- Reduces throttling

Limitations:

- Cannot fix poor partition-key design
- Cannot eliminate extremely hot keys

---

# CloudWatch Investigation Workflow

```text
Alert

↓

ReadThrottleEvents

↓

Identify Hot Partition

↓

Review Access Pattern

↓

Redesign If Necessary
```

---

# Common Symptoms

Applications may experience:

- Increased latency
- Timeouts
- Retry storms
- Failed writes
- Failed reads

---

# Retry Storm

```text
Throttle

↓

Retry

↓

Throttle

↓

Retry

↓

More Traffic

↓

Worse Throttling
```

Retries without backoff make the problem worse.

---

# Exponential Backoff

Correct strategy:

```text
Failure

↓

Wait

↓

Retry

↓

Wait Longer

↓

Retry
```

Never retry immediately.

---

# Jitter

Instead of:

```text
100 ms

200 ms

400 ms
```

Use:

```text
Randomized Delay

↓

Prevents Retry Storms
```

AWS SDKs already implement this behavior.

---

# Capacity Planning

Provisioned Mode

```text
Estimate Traffic

↓

Configure RCUs/WCUs

↓

Monitor

↓

Adjust
```

---

# On-Demand Planning

Good for:

- Unknown traffic
- Startups
- Bursty workloads

Not ideal for:

- Constant high-throughput systems where Provisioned capacity may be more cost-effective.

---

# Production Example

Poor design:

```text
Partition Key

status
```

Values:

```text
OPEN

CLOSED
```

Only two partitions become extremely busy.

---

Better design:

```text
customer_id
```

Millions of unique values.

Traffic distributes naturally.

---

# Another Production Example

Bad:

```text
Today's Date

↓

2026-07-26

↓

Millions of Requests
```

Good:

```text
customer_id#date
```

Traffic spreads across many partitions.

---

# Mitigation Strategies

- Improve partition key design.
- Use high-cardinality keys.
- Avoid sequential keys.
- Enable Auto Scaling.
- Consider On-Demand billing.
- Cache frequently accessed data.
- Use DynamoDB Accelerator (DAX) for read-heavy workloads.

---

# DAX Architecture

```text
Application

      │

      ▼

DAX Cache

      │

Cache Hit

      ▼

Response

──────────────

Cache Miss

↓

DynamoDB
```

Reduces read pressure.

---

# Monitoring Checklist

Monitor:

- ReadThrottleEvents
- WriteThrottleEvents
- Latency
- Retry count
- Capacity utilization
- CloudWatch alarms

---

# Production Architecture

```text
Application

      │

      ▼

Load Balancer

      │

      ▼

Backend Service

      │

      ▼

DynamoDB

      │

      ▼

CloudWatch

      │

      ▼

Alarm

      │

      ▼

Operations Team
```

---

# Troubleshooting Checklist

```text
Application Slow?

↓

CloudWatch

↓

Throttle Metrics

↓

Describe Table

↓

Billing Mode

↓

Capacity

↓

Partition Key Design

↓

Root Cause
```

---

# Performance Considerations

- Design for even traffic distribution.
- Avoid sequential partition keys.
- Monitor throttling continuously.
- Cache hot data.
- Use Query instead of Scan.
- Review access patterns before increasing capacity.

---

# Best Practices

- Design high-cardinality partition keys.
- Enable CloudWatch alarms.
- Use exponential backoff with jitter.
- Monitor adaptive capacity behavior.
- Benchmark workloads before production.
- Review partition-key design during architecture reviews.

---

# Common Mistakes

## Increasing Capacity Without Investigation

More capacity does not solve poor partition-key design.

---

## Ignoring Hot Keys

One frequently accessed key can overload an otherwise healthy table.

---

## Retrying Immediately

Immediate retries amplify throttling.

Always use exponential backoff with jitter.

---

## Using Sequential Keys

Keys such as:

```text
1

2

3

4

5
```

can concentrate traffic and should generally be avoided as partition keys.

---

# Interview Notes

### What is a hot partition?

A hot partition is a physical partition receiving disproportionately high traffic, causing throttling even when overall table capacity appears sufficient.

---

### Why does `ProvisionedThroughputExceededException` occur?

It occurs when DynamoDB cannot serve additional requests because the available throughput for a partition or table has been exceeded.

---

### Can On-Demand tables throttle?

Yes. Although On-Demand automatically scales, individual partitions still have throughput limits. Extremely uneven traffic or sudden spikes can still cause throttling.

---

### What is Adaptive Capacity?

Adaptive Capacity is a DynamoDB feature that automatically reallocates capacity to partitions experiencing higher traffic. It helps absorb uneven workloads but cannot compensate for fundamentally poor partition-key design.

---

### How do you fix a hot partition?

- Redesign the partition key.
- Increase key cardinality.
- Introduce sharding if appropriate.
- Cache frequently read data.
- Review access patterns rather than simply increasing capacity.

---

# Key Takeaways

- Throttling is often a symptom of poor data distribution rather than insufficient table capacity.
- Hot keys and hot partitions are among the most common causes of production performance issues in DynamoDB.
- CloudWatch metrics, AWS CLI diagnostics, and thoughtful partition-key design are essential for identifying and resolving throttling.
- Adaptive Capacity, DAX, caching, and exponential backoff help mitigate throttling, but good data modeling remains the most effective long-term solution.
- Senior engineers focus on access patterns and partition design before scaling capacity.