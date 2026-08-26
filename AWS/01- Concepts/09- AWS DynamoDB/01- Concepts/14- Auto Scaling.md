# 14 - Auto Scaling

## Overview

One of the primary goals of cloud computing is to eliminate the need for manual infrastructure management.

Imagine deploying an application that normally serves **500 requests per second**, but every Friday evening traffic increases to **25,000 requests per second**. If your DynamoDB table is configured with insufficient throughput, requests will be throttled. On the other hand, permanently provisioning capacity for peak traffic would waste money during normal operation.

DynamoDB solves this problem through **Auto Scaling**.

Auto Scaling continuously monitors table utilization and automatically adjusts provisioned Read Capacity Units (RCUs) and Write Capacity Units (WCUs) to match the application's workload.

Instead of guessing future traffic patterns, developers define scaling policies, and AWS adjusts throughput automatically.

---

# Why Auto Scaling Exists

Consider an online shopping platform.

Normal traffic:

```text
Morning

↓

500 Requests/sec
```

Lunch:

```text
↓

2,000 Requests/sec
```

Evening Sale:

```text
↓

20,000 Requests/sec
```

Night:

```text
↓

300 Requests/sec
```

If the table always remained at:

```text
20,000 RCUs
```

Most of those resources would sit idle for much of the day.

If it stayed at:

```text
500 RCUs
```

The evening sale would overwhelm the table.

Auto Scaling dynamically adjusts throughput between these extremes.

---

# Provisioned Capacity Without Auto Scaling

Suppose a table is configured with:

```text
500 RCUs

200 WCUs
```

Traffic increases.

```text
500

↓

2,000

↓

10,000 Requests/sec
```

The table cannot keep up.

Result:

```text
ProvisionedThroughputExceededException
```

Requests begin to fail or experience retries.

Someone must manually increase capacity.

---

# Provisioned Capacity With Auto Scaling

Now consider the same workload.

```text
500 RCUs

↓

CloudWatch Detects Increased Utilization

↓

Auto Scaling

↓

2,000 RCUs

↓

5,000 RCUs

↓

10,000 RCUs
```

Applications continue operating without manual intervention.

As traffic decreases:

```text
10,000 RCUs

↓

5,000 RCUs

↓

2,000 RCUs

↓

500 RCUs
```

AWS automatically scales capacity back down.

---

# How Auto Scaling Works

Auto Scaling is built on three AWS services working together.

```text
Application

↓

DynamoDB

↓

CloudWatch Metrics

↓

Auto Scaling Policy

↓

Increase or Decrease RCUs/WCUs
```

Each component has a specific responsibility.

---

# Step 1 – CloudWatch Collects Metrics

CloudWatch continuously monitors metrics such as:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ReadThrottleEvents
- WriteThrottleEvents

These metrics represent the actual workload.

---

# Step 2 – Target Utilization

Instead of specifying exactly when scaling should occur, developers configure a **Target Utilization**.

Example:

```text
70%
```

Meaning:

> Try to keep average utilization around 70%.

If actual utilization exceeds the target:

```text
Current Utilization

85%
```

Auto Scaling increases throughput.

If utilization drops:

```text
Current Utilization

20%
```

Auto Scaling reduces throughput.

---

# Step 3 – Capacity Adjustment

Suppose the configuration is:

```text
Minimum RCUs

100
```

```text
Maximum RCUs

10,000
```

Current capacity:

```text
500 RCUs
```

Traffic spikes.

CloudWatch reports:

```text
95% Utilization
```

Auto Scaling increases capacity.

```text
500

↓

1000

↓

2000

↓

4000 RCUs
```

The application remains responsive.

---

# Minimum and Maximum Capacity

Every Auto Scaling policy defines boundaries.

Example:

```text
Minimum

100 RCUs
```

```text
Maximum

20,000 RCUs
```

Auto Scaling never exceeds these limits.

This prevents:

- Unexpected costs
- Unlimited scaling
- Misconfigured applications

Choosing realistic limits is an important architectural decision.

---

# Scaling Reads and Writes Independently

Read traffic and write traffic often grow differently.

For example:

```text
Reads

50,000/sec
```

```text
Writes

500/sec
```

Auto Scaling allows separate policies.

Example:

```text
Read Target

70%
```

```text
Write Target

50%
```

This provides more efficient resource allocation.

---

# Auto Scaling Response Time

One common misconception is that Auto Scaling reacts instantly.

It does not.

The process is:

```text
Traffic Increases

↓

CloudWatch Collects Metrics

↓

Scaling Decision

↓

Capacity Adjustment
```

This process requires time.

During sudden traffic spikes, temporary throttling may still occur before scaling completes.

Applications should therefore implement:

- Retries
- Exponential Backoff
- Jitter

Auto Scaling is not a substitute for resilient application design.

---

# Auto Scaling vs On-Demand Mode

These concepts are often confused.

## On-Demand

```text
Developer

↓

No Capacity Configuration

↓

AWS Handles Everything
```

Capacity automatically adjusts without developer-defined limits.

---

## Provisioned + Auto Scaling

```text
Developer

↓

Defines Limits

↓

AWS Adjusts Capacity

↓

Within Those Limits
```

The application has more predictable costs and greater operational control.

---

# Auto Scaling vs Adaptive Capacity

Another common point of confusion.

## Adaptive Capacity

Focuses on:

```text
One Busy Partition
```

It redistributes internal resources across partitions.

---

## Auto Scaling

Focuses on:

```text
Entire Table Capacity
```

It increases or decreases total RCUs and WCUs.

| Feature | Auto Scaling | Adaptive Capacity |
|----------|--------------|------------------|
| Increases Total RCUs/WCUs | ✅ Yes | ❌ No |
| Redistributes Internal Capacity | ❌ No | ✅ Yes |
| Configurable | ✅ Yes | ❌ Automatic |
| Uses CloudWatch | ✅ Yes | Internal AWS Logic |

Both features complement one another.

---

# Real-World Example

An online retailer announces a Black Friday sale.

Traffic:

```text
Midnight

↓

2,000 Requests/sec
```

8:00 AM

```text
↓

15,000 Requests/sec
```

10:00 AM

```text
↓

80,000 Requests/sec
```

Without Auto Scaling:

- Throttling
- Failed requests
- Poor customer experience

With Auto Scaling:

CloudWatch detects increased utilization.

Provisioned throughput gradually increases.

The application continues serving customers.

After the sale:

```text
80,000

↓

15,000

↓

2,000 Requests/sec
```

Capacity automatically decreases, reducing infrastructure costs.

---

# Best Practices

- Configure realistic minimum and maximum capacity.
- Use separate scaling policies for reads and writes.
- Monitor CloudWatch metrics regularly.
- Load test applications before production.
- Combine Auto Scaling with Adaptive Capacity.
- Implement retry logic because scaling is not instantaneous.
- Review scaling policies periodically as workloads evolve.

---

# Common Mistakes

## Setting Maximum Capacity Too Low

Suppose the maximum is:

```text
1,000 RCUs
```

Traffic requires:

```text
8,000 RCUs
```

Auto Scaling cannot exceed the configured limit.

Throttling continues.

---

## Setting Maximum Capacity Too High

While this avoids throttling, it can lead to unexpectedly high cloud costs if traffic spikes.

---

## Assuming Auto Scaling Reacts Immediately

Scaling decisions require CloudWatch metrics and policy evaluation.

Applications must tolerate short-lived traffic bursts.

---

## Ignoring CloudWatch

Auto Scaling should not be considered "set and forget."

Monitoring scaling events helps identify inefficient workloads and opportunities for schema optimization.

---

# Architecture Perspective

A common production deployment follows this model:

```text
Application

↓

API Gateway

↓

Lambda / ECS / EC2

↓

DynamoDB

↓

CloudWatch Metrics

↓

Application Auto Scaling

↓

Provisioned Capacity Adjustments
```

Notice that Auto Scaling is part of the operational control plane rather than the request path.

It adjusts throughput over time but does not process application requests directly.

---

# Interview Notes

A common interview question is:

> **If Auto Scaling automatically increases throughput, why do applications still need retry logic?**

Because Auto Scaling is **reactive**, not proactive.

It first observes increased utilization through CloudWatch metrics, evaluates the scaling policy, and then updates the table's capacity. During that interval, requests may exceed the currently provisioned throughput and be throttled.

Production applications therefore combine Auto Scaling with exponential backoff and retries to handle short-term traffic spikes gracefully.

Another common interview question is:

> **When would you choose On-Demand instead of Provisioned Capacity with Auto Scaling?**

Choose On-Demand when traffic is highly unpredictable or for new applications where usage patterns are unknown. Choose Provisioned Capacity with Auto Scaling when workloads are relatively predictable and cost optimization is important.

---

# Key Takeaways

- Auto Scaling automatically adjusts provisioned RCUs and WCUs based on workload.
- It relies on CloudWatch metrics and target utilization policies.
- Read and write capacity can scale independently.
- Auto Scaling operates within configured minimum and maximum limits.
- It is reactive, so applications must still implement retries and exponential backoff.
- Auto Scaling increases total table throughput, while Adaptive Capacity redistributes throughput across partitions.
- Combining good schema design, Adaptive Capacity, and Auto Scaling provides the most resilient and cost-effective DynamoDB deployments.