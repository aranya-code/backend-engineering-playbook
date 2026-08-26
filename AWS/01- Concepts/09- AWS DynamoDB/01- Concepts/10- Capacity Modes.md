# 10 - Capacity Modes (On-Demand vs Provisioned)

## Overview

In the previous chapter, we learned that every read and write operation consumes **Read Capacity Units (RCUs)** and **Write Capacity Units (WCUs)**.

The next logical question is:

> **How does DynamoDB know how many RCUs and WCUs my application is allowed to consume?**

The answer depends on the **Capacity Mode** configured for the table.

DynamoDB offers two different capacity models:

- **On-Demand Capacity**
- **Provisioned Capacity**

Both execute the same read and write operations. The difference lies in **how throughput is allocated, how scaling occurs, and how billing works**.

Choosing the correct capacity mode is a production architecture decision because it directly impacts:

- Performance
- Scalability
- Cost
- Operational overhead
- Application reliability

---

# Why Two Capacity Modes Exist

Consider two different applications.

Application A

```text
Internal HR Portal

09:00 AM → Heavy Traffic

10:00 AM → Almost Idle

06:00 PM → No Users
```

Application B

```text
Payment API

24 Hours

Thousands of Requests Every Second
```

Both applications use DynamoDB.

Should AWS allocate the same amount of capacity to both?

Obviously not.

One has highly unpredictable traffic.

The other has stable, predictable traffic.

This is exactly why DynamoDB provides two capacity models.

---

# Capacity Modes

```text
                DynamoDB

                    │

        ┌───────────┴───────────┐

        │                       │

 Provisioned             On-Demand
```

Both modes store data identically.

Only the capacity management strategy changes.

---

# On-Demand Capacity Mode

On-Demand mode is the simplest option.

Instead of specifying throughput in advance, developers simply send requests.

DynamoDB automatically allocates enough capacity to satisfy the workload.

```text
Application

↓

Read

↓

Write

↓

DynamoDB

↓

Automatically Allocates Capacity
```

There are:

- No RCU planning
- No WCU planning
- No manual scaling
- No capacity configuration

AWS manages everything.

---

# How On-Demand Works

Imagine a startup launches a new application.

Day 1

```text
50 Requests / Second
```

A month later

```text
5,000 Requests / Second
```

A marketing campaign succeeds.

```text
200,000 Requests / Second
```

Developers do nothing.

DynamoDB automatically increases throughput.

Later, traffic drops.

```text
100 Requests / Second
```

Capacity automatically scales down.

This elasticity makes On-Demand ideal for unpredictable workloads.

---

# Advantages of On-Demand

## No Capacity Planning

Developers never estimate traffic.

No calculations are required.

---

## Automatic Scaling

Traffic spikes are automatically handled.

Applications continue operating without manual intervention.

---

## Pay Only for Requests

Billing depends on actual requests processed rather than reserved throughput.

If the application is idle, costs remain relatively low because unused capacity is not reserved.

---

## Ideal for New Applications

Most startups have unpredictable traffic.

On-Demand allows developers to focus on product development instead of infrastructure management.

---

# Disadvantages of On-Demand

Although extremely convenient, On-Demand is not always the cheapest option.

Large enterprise systems with stable workloads often pay more compared to Provisioned Capacity.

Additionally:

- Less predictable monthly costs
- Higher cost per request
- Less control over throughput planning

---

# Provisioned Capacity Mode

Provisioned Capacity works differently.

Instead of allowing DynamoDB to decide throughput automatically, developers specify exactly how much capacity the table should have.

Example

```text
Read Capacity

100 RCUs

Write Capacity

50 WCUs
```

DynamoDB reserves these resources continuously.

Whether they are used or not, they remain available.

---

# How Provisioned Capacity Works

Suppose an API consistently receives:

```text
100 Reads / Second

20 Writes / Second
```

The architect configures:

```text
120 RCUs

30 WCUs
```

As long as requests remain within these limits, performance is stable.

However, if demand suddenly increases beyond the configured capacity:

```text
120 RCUs Configured

↓

250 RCUs Requested
```

Some requests may be throttled until additional capacity becomes available.

---

# Advantages of Provisioned Capacity

## Lower Cost for Predictable Workloads

If traffic remains relatively constant, Provisioned Capacity is often significantly cheaper.

This is why many enterprise systems use it.

---

## Predictable Monthly Billing

Infrastructure costs remain relatively stable.

Finance teams appreciate predictable cloud expenses.

---

## Fine-Grained Control

Architects decide exactly how much throughput is available.

This provides greater operational control.

---

# Disadvantages of Provisioned Capacity

Provisioned Capacity requires planning.

Developers must:

- Estimate traffic
- Monitor usage
- Increase capacity before large events
- Avoid over-provisioning

Improper planning can result in:

- Higher costs
- Throttled requests
- Wasted capacity

---

# Auto Scaling

Provisioned Capacity does not necessarily mean fixed capacity forever.

AWS supports **Auto Scaling**.

```text
Current Capacity

↓

CloudWatch Metrics

↓

Target Utilization

↓

Increase Capacity

↓

Decrease Capacity
```

Auto Scaling adjusts RCUs and WCUs automatically within configured minimum and maximum limits.

Example

Minimum

```text
100 RCUs
```

Maximum

```text
3000 RCUs
```

If traffic grows gradually, Auto Scaling increases provisioned throughput.

When demand decreases, capacity is reduced.

This combines predictable pricing with automatic elasticity.

---

# On-Demand vs Provisioned

| Feature | On-Demand | Provisioned |
|----------|-----------|-------------|
| Capacity Planning | None | Required |
| Scaling | Automatic | Manual or Auto Scaling |
| Billing | Per Request | Reserved Throughput |
| Predictable Cost | No | Yes |
| Best For | Unpredictable Traffic | Stable Traffic |
| Operational Overhead | Very Low | Moderate |

---

# Choosing the Right Capacity Mode

## Choose On-Demand When

- Building a new application
- Traffic is unpredictable
- Seasonal workloads exist
- Development environments
- Proof of Concepts
- Internal tools with irregular usage

---

## Choose Provisioned When

- Traffic is stable
- Enterprise production systems
- Long-running APIs
- Financial applications
- Large-scale SaaS platforms
- Cost optimization is important

---

# Real-World Example

## Startup

A new food delivery application launches.

No one knows whether traffic will be:

```text
500 Users

or

500,000 Users
```

Using Provisioned Capacity would require guessing future demand.

On-Demand eliminates that uncertainty.

---

## Enterprise Payroll System

Employees receive salaries on the last day of every month.

Traffic pattern:

```text
Normal

↓

Normal

↓

Payroll Day

↓

Large Spike

↓

Normal
```

Provisioned Capacity combined with Auto Scaling provides predictable costs while still handling scheduled spikes.

---

# Monitoring Capacity Modes

Regardless of capacity mode, CloudWatch remains essential.

Important metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ThrottledRequests
- SuccessfulRequestLatency
- ReadThrottleEvents
- WriteThrottleEvents

These metrics help determine whether the current capacity mode remains appropriate.

---

# Common Mistakes

## Choosing Provisioned Too Early

Many teams begin with Provisioned Capacity before understanding real traffic patterns.

This often results in either:

- Over-provisioning
- Under-provisioning

On-Demand is frequently the better initial choice.

---

## Ignoring Auto Scaling

Provisioned Capacity without Auto Scaling often leads to avoidable throttling.

---

## Confusing Storage with Capacity

Capacity determines throughput.

Storage determines data volume.

They are independent concepts.

---

## Assuming On-Demand is Always More Expensive

Although the per-request price is higher, On-Demand may cost less overall for low-volume or unpredictable workloads because no unused capacity is reserved.

Cost comparisons should always be based on actual traffic patterns.

---

# Architecture Perspective

A common migration path is:

```text
Development

↓

On-Demand

↓

Traffic Becomes Predictable

↓

Provisioned + Auto Scaling

↓

Capacity Optimization
```

Many successful production systems follow this progression rather than starting with Provisioned Capacity.

---

# Interview Notes

A common interview question is:

> **If On-Demand automatically scales, why would anyone choose Provisioned Capacity?**

Because many enterprise applications have predictable workloads.

Provisioned Capacity reserves throughput at a lower cost than continuously paying per request. When combined with Auto Scaling, it provides both cost efficiency and elasticity.

The decision is primarily an **economic optimization**, not a technical limitation.

---

# Key Takeaways

- Capacity Mode determines how throughput is allocated and billed.
- On-Demand automatically scales and charges per request.
- Provisioned Capacity reserves RCUs and WCUs in advance.
- Auto Scaling adds elasticity to Provisioned Capacity.
- On-Demand is ideal for unpredictable workloads.
- Provisioned Capacity is generally more cost-effective for stable, predictable traffic.
- Capacity mode should be chosen based on workload characteristics, operational requirements, and cost goals rather than developer preference.