# 03 - Auto Scaling Deep Dive

## Overview

Provisioning the correct capacity for a DynamoDB table is challenging.

If you provision **too little**, requests get throttled.

If you provision **too much**, you pay for unused capacity.

To solve this problem, DynamoDB integrates with **Application Auto Scaling**, which automatically adjusts the provisioned read and write capacity based on workload demand.

Unlike On-Demand mode, Auto Scaling only works with **Provisioned Capacity** and provides a balance between predictable performance and cost optimization.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How DynamoDB Auto Scaling works
- Target Tracking Policies
- Scale Out vs Scale In
- CloudWatch integration
- Cooldown periods
- Auto Scaling workflow
- Production tuning
- Common scaling issues
- Best practices
- Interview questions

---

# What is Auto Scaling?

Auto Scaling automatically increases or decreases the provisioned capacity of a table or secondary index based on utilization.

```text
              Traffic

                 │

                 ▼

      CloudWatch Metrics

                 │

                 ▼

      Application Auto Scaling

                 │

                 ▼

     UpdateTable API

                 │

                 ▼

     New Provisioned Capacity
```

The application does not need to change.

---

# Why Auto Scaling?

Consider an e-commerce website.

Traffic throughout the day:

```text
Morning

↓

Low

↓

Lunch

↓

Medium

↓

Evening Sale

↓

Very High

↓

Night

↓

Low
```

Static capacity means:

- Over-provisioning during low traffic
- Under-provisioning during peak traffic

Auto Scaling solves this automatically.

---

# Auto Scaling Architecture

```text
                 Users

                    │

                    ▼

             Application

                    │

                    ▼

              DynamoDB Table

                    │

      Consumed Capacity Metrics

                    │

                    ▼

             CloudWatch

                    │

                    ▼

      Application Auto Scaling

                    │

                    ▼

         Update Provisioned Capacity
```

---

# Components

Auto Scaling consists of four main components.

| Component | Purpose |
|-----------|----------|
| DynamoDB | Stores data |
| CloudWatch | Collects utilization metrics |
| Application Auto Scaling | Makes scaling decisions |
| IAM Role | Allows scaling operations |

---

# Target Tracking Policy

Auto Scaling works by maintaining a target utilization.

Example:

```text
Target Utilization

↓

70%
```

If utilization exceeds 70%:

```text
Increase Capacity
```

If utilization drops well below 70%:

```text
Decrease Capacity
```

---

# Example

Current Provisioned Capacity

```text
100 RCU
```

Current Consumption

```text
85 RCU
```

Utilization

```text
85%
```

Target

```text
70%
```

Auto Scaling increases provisioned capacity until utilization approaches the target.

---

# Scale Out

When traffic increases:

```text
Traffic

↓

Consumed Capacity

↓

Above Target

↓

Scale Out

↓

More RCUs/WCUs
```

Example:

```text
100 RCU

↓

150 RCU

↓

250 RCU
```

---

# Scale In

When traffic decreases:

```text
Low Utilization

↓

Scale In

↓

Reduce Capacity
```

Example:

```text
500 WCU

↓

300 WCU

↓

150 WCU
```

This reduces infrastructure cost.

---

# Auto Scaling Workflow

```text
Application

↓

Traffic

↓

Consumed Capacity

↓

CloudWatch Metric

↓

Target Tracking Policy

↓

Scaling Decision

↓

UpdateTable

↓

New Capacity
```

---

# Read and Write Scaling

Read and write capacity scale independently.

Example:

```text
Read Capacity

↓

Auto Scaling

────────────

Write Capacity

↓

Auto Scaling
```

A write-heavy workload may require only WCU scaling.

---

# Secondary Index Scaling

Global Secondary Indexes (GSIs) have independent capacity.

```text
Table

↓

100 WCU

────────────

GSI

↓

50 WCU
```

Each can have its own Auto Scaling policy.

---

# Minimum and Maximum Capacity

Every scaling policy defines limits.

Example:

```text
Minimum

↓

50 RCU

────────────

Maximum

↓

1000 RCU
```

Auto Scaling will never exceed these limits.

---

# Cooldown Period

Scaling is not instantaneous.

Without cooldown:

```text
Scale

↓

Scale

↓

Scale

↓

Oscillation
```

With cooldown:

```text
Scale

↓

Wait

↓

Observe

↓

Scale Again
```

Cooldown prevents frequent scaling actions.

---

# CloudWatch Metrics

Auto Scaling primarily monitors:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits
```

Additional metrics include:

- ReadThrottleEvents
- WriteThrottleEvents
- SuccessfulRequestLatency

---

# Scaling Timeline

```text
Traffic Spike

↓

Capacity Usage Increases

↓

CloudWatch Detects

↓

Target Tracking Policy

↓

Scaling Decision

↓

UpdateTable

↓

New Capacity
```

This process typically takes a short amount of time and is **not instantaneous**, so sudden traffic spikes may still experience temporary throttling.

---

# Production Example

An online shopping platform:

```text
Normal

↓

200 RCU

────────────

Black Friday

↓

2000 RCU

────────────

After Sale

↓

250 RCU
```

Auto Scaling adjusts capacity without manual intervention.

---

# Auto Scaling Limitations

Auto Scaling is reactive.

It responds **after** utilization increases.

Therefore:

```text
Sudden Spike

↓

Temporary Throttling

↓

Scale Out

↓

Recovery
```

For highly predictable events:

- Product launches
- Flash sales
- Ticket booking
- Live streaming

Manually increasing capacity beforehand may be preferable.

---

# Auto Scaling vs On-Demand

| Feature | Auto Scaling | On-Demand |
|----------|-------------|-----------|
| Requires Capacity Planning | Yes | No |
| Uses Provisioned Capacity | Yes | No |
| Automatic Scaling | Yes | Yes |
| Cost Predictability | High | Usage-Based |
| Best For | Stable workloads with variation | Unknown workloads |

---

# Auto Scaling and Partitions

Increasing RCUs does not automatically eliminate hot partitions.

```text
Hot Partition

↓

More Table Capacity

↓

Still Hot
```

Proper partition key design remains essential.

---

# Production Architecture

```text
                 Internet

                     │

                     ▼

              Application

                     │

                     ▼

              DynamoDB Table

                     │

     Consumed Capacity Metrics

                     │

                     ▼

              CloudWatch

                     │

                     ▼

      Application Auto Scaling

                     │

                     ▼

          UpdateTable API

                     │

                     ▼

       Increased/Reduced Capacity
```

---

# Best Practices

- Start with realistic minimum capacity.
- Set reasonable maximum limits to prevent unexpected costs.
- Monitor CloudWatch dashboards regularly.
- Enable Auto Scaling for both tables and GSIs.
- Use separate scaling policies for reads and writes.
- Combine Auto Scaling with good partition key design.
- Pre-scale capacity before planned traffic spikes.

---

# Common Mistakes

## Setting the Target Utilization Too High

Example:

```text
95%
```

This leaves little room for traffic bursts and increases the likelihood of throttling.

Typical production targets range between **60% and 80%**, depending on workload characteristics.

---

## Ignoring GSIs

Many teams configure Auto Scaling only for the base table.

A throttled GSI can slow application queries even if the table has sufficient capacity.

---

## Assuming Scaling is Instant

Scaling requires:

- Metric collection
- Policy evaluation
- Capacity update

Applications should implement:

- Exponential backoff
- Retry logic
- Graceful error handling

---

## Unlimited Maximum Capacity

Setting a very high maximum capacity without monitoring can lead to unexpectedly high costs during abnormal traffic or application bugs.

---

# Production Considerations

Large enterprises often configure:

```text
Provisioned Capacity

+

Auto Scaling

+

CloudWatch Alarms

+

AWS Budgets

+

Performance Dashboards
```

Operations teams continuously monitor utilization, throttling events, scaling activity, and costs to ensure efficient operation.

---

# Interview Notes

A common interview question is:

> **Does DynamoDB Auto Scaling work with On-Demand tables?**

No. Auto Scaling is available only for **Provisioned Capacity** tables and indexes. On-Demand tables manage scaling automatically without Auto Scaling policies.

---

Another common question is:

> **What triggers Auto Scaling?**

Auto Scaling uses CloudWatch metrics and Target Tracking Policies to monitor consumed capacity. When utilization deviates from the configured target, Application Auto Scaling adjusts the provisioned capacity.

---

Another common question is:

> **Why can throttling still occur even with Auto Scaling enabled?**

Auto Scaling is reactive. During sudden traffic spikes, requests may be throttled briefly before the scaling action completes. Retry logic and exponential backoff are recommended.

---

Another common question is:

> **Can GSIs have independent Auto Scaling policies?**

Yes. Each Global Secondary Index can have separate read and write Auto Scaling policies, allowing independent scaling based on its workload.

---

# Key Takeaways

- Auto Scaling automatically adjusts provisioned RCUs and WCUs based on CloudWatch metrics.
- It works only with **Provisioned Capacity**, not On-Demand mode.
- Target Tracking Policies maintain utilization around a configured percentage.
- Read and write capacities, as well as GSIs, can scale independently.
- Auto Scaling is reactive, so applications should still implement retries and exponential backoff.
- Effective Auto Scaling requires good monitoring, realistic limits, and proper partition key design.