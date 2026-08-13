# 01 - Capacity Modes (Provisioned vs On-Demand)

## Overview

One of the most important architectural decisions when designing a DynamoDB table is choosing the **capacity mode**.

Capacity mode determines **how DynamoDB allocates throughput** for read and write requests and directly impacts:

- Performance
- Scalability
- Cost
- Operational overhead

Amazon DynamoDB offers two capacity modes:

- **Provisioned Capacity**
- **On-Demand Capacity**

Choosing the wrong mode can lead to unnecessary costs or request throttling, while the right choice enables predictable performance and efficient scaling.

---

# Learning Objectives

After completing this chapter, you will understand:

- What capacity modes are
- How Provisioned Capacity works
- How On-Demand Capacity works
- Differences between the two modes
- Cost implications
- Performance characteristics
- Production use cases
- Best practices for selecting the appropriate mode

---

# Why Capacity Management Exists

Unlike traditional databases where you manage servers, DynamoDB abstracts infrastructure but still needs to allocate resources to handle requests.

```text
Application

↓

Read / Write Requests

↓

DynamoDB Capacity

↓

Storage Partitions
```

Capacity mode determines how DynamoDB prepares for incoming traffic.

---

# Capacity Modes

```text
                DynamoDB

                     │

     ┌───────────────┴───────────────┐

     ▼                               ▼

Provisioned Capacity          On-Demand Capacity
```

Both provide high availability and low latency, but they manage throughput differently.

---

# Provisioned Capacity

With Provisioned Capacity, you specify how many:

- Read Capacity Units (RCUs)
- Write Capacity Units (WCUs)

your table should support.

Example:

```text
Orders Table

↓

100 RCU

↓

50 WCU
```

DynamoDB reserves sufficient resources to handle this workload.

---

# How Provisioned Capacity Works

```text
Application

↓

100 Requests/sec

↓

Provisioned Capacity

↓

DynamoDB
```

If traffic stays within the provisioned capacity, requests are processed with low latency.

If traffic exceeds the provisioned limits, DynamoDB may throttle requests.

---

# On-Demand Capacity

With On-Demand mode, you do **not** specify RCUs or WCUs.

Instead:

```text
Application

↓

Traffic

↓

Automatic Scaling

↓

DynamoDB
```

DynamoDB automatically allocates capacity based on request volume.

You pay only for the read and write requests you actually consume.

---

# Internal Scaling Behavior

Provisioned:

```text
100 WCU

↓

Reserved

↓

Traffic Uses Reserved Capacity
```

On-Demand:

```text
Traffic

↓

Automatic Capacity Allocation

↓

Scaling Managed by AWS
```

---

# Comparison

| Feature | Provisioned | On-Demand |
|----------|-------------|-----------|
| Capacity Planning | Required | Not Required |
| Auto Scaling | Optional | Automatic |
| Cost Predictability | High | Usage-Based |
| Handles Traffic Spikes | With Auto Scaling or Over-Provisioning | Automatically |
| Operational Overhead | Higher | Lower |
| Best For | Predictable Workloads | Variable or Unknown Workloads |

---

# Provisioned Capacity Use Cases

Provisioned mode is ideal for applications with predictable traffic patterns.

Examples:

- Payroll systems
- ERP applications
- Internal business tools
- Banking systems with known transaction volumes
- Manufacturing systems

Example traffic pattern:

```text
9 AM

↓

High

────────────

6 PM

↓

Low
```

Capacity can be planned and adjusted accordingly.

---

# On-Demand Capacity Use Cases

On-Demand mode excels when workloads are unpredictable.

Examples:

- New applications
- Startups
- Marketing campaigns
- Viral social media applications
- Event registration platforms
- Seasonal e-commerce

Traffic pattern:

```text
Low

↓

Very High

↓

Low

↓

Massive Spike
```

DynamoDB automatically adjusts capacity.

---

# Switching Capacity Modes

Capacity modes are **not permanent**.

```text
Provisioned

↓

Switch

↓

On-Demand
```

or

```text
On-Demand

↓

Switch

↓

Provisioned
```

This allows teams to adapt as application traffic evolves.

---

# Production Architecture

```text
              Application

                    │

         Read / Write Requests

                    │

              DynamoDB Table

         ┌──────────┴──────────┐

         ▼                     ▼

Provisioned Mode       On-Demand Mode
```

The choice depends on workload characteristics rather than application architecture.

---

# Cost Considerations

Provisioned Capacity:

- Pay for allocated capacity, even if unused.
- More cost-effective for stable, predictable workloads.

On-Demand Capacity:

- Pay per request.
- Eliminates over-provisioning.
- Often more economical for unpredictable or bursty traffic.

Choosing the wrong mode can significantly affect monthly costs.

---

# Best Practices

- Start new applications with On-Demand Capacity.
- Switch to Provisioned Capacity once traffic patterns become predictable.
- Use Auto Scaling with Provisioned Capacity to handle moderate fluctuations.
- Monitor CloudWatch metrics regularly.
- Review capacity utilization during architecture reviews.
- Test applications under realistic load before production deployment.

---

# Common Mistakes

## Choosing Provisioned Capacity Too Early

New applications often have unpredictable traffic.

Starting with On-Demand reduces operational complexity.

---

## Ignoring Capacity Planning

Provisioned tables without monitoring may experience throttling.

Always monitor utilization and adjust capacity proactively.

---

## Assuming On-Demand Is Unlimited

Although On-Demand scales automatically, applications should still be designed to handle retries, exponential backoff, and service quotas.

---

## Never Re-Evaluating Capacity Mode

Traffic patterns change over time.

Regularly review whether the selected capacity mode remains appropriate.

---

# Production Considerations

Many organizations follow this lifecycle:

```text
Development

↓

On-Demand

↓

Growing Traffic

↓

Provisioned + Auto Scaling

↓

Large Enterprise

↓

Provisioned + Capacity Planning + Monitoring
```

This balances operational simplicity during early growth with cost optimization at scale.

---

# Interview Notes

A common interview question is:

> **When would you choose On-Demand Capacity over Provisioned Capacity?**

Use On-Demand when traffic is unpredictable, difficult to forecast, or highly variable. It minimizes operational effort by automatically scaling with demand.

---

Another common question is:

> **Why would an enterprise choose Provisioned Capacity?**

Provisioned Capacity offers predictable performance and can reduce costs for workloads with stable, consistent traffic. It also allows fine-grained capacity planning and optimization.

---

Another common question is:

> **Can you change the capacity mode of a DynamoDB table?**

Yes. DynamoDB allows switching between Provisioned and On-Demand modes, enabling applications to adapt as workload characteristics change.

---

# Key Takeaways

- DynamoDB offers two capacity modes: Provisioned and On-Demand.
- Provisioned Capacity is best for predictable workloads with stable traffic.
- On-Demand Capacity automatically scales to match request volume and is ideal for unpredictable workloads.
- Capacity mode selection directly affects performance, cost, and operational overhead.
- Monitor usage patterns regularly and adjust capacity strategy as applications evolve.
- Understanding capacity modes is fundamental to designing cost-efficient, high-performance DynamoDB systems.