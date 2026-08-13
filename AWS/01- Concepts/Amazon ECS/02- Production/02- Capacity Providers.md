# ECS Capacity Providers

# What Are Capacity Providers?

Capacity Providers determine:

```text
Where ECS Tasks Run
```

Think of them as a scheduling layer between:

```text
ECS Service
      ↓
Compute Resources
```

---

# Why Capacity Providers Exist

Before Capacity Providers:

```text
Launch Type
     ↓
EC2

or

Fargate
```

Rigid choice.

---

Modern systems require:

- Cost optimization
- Mixed infrastructure
- High availability
- Flexible scheduling

Capacity Providers solve these problems.

---

# ECS Scheduling Architecture

```text
ECS Service
      ↓
Capacity Provider
      ↓
Compute Resources
```

ECS decides where tasks should run based on provider strategy.

---

# Supported Capacity Providers

ECS supports:

```text
EC2
Fargate
Fargate Spot
```

---

# EC2 Capacity Provider

Uses EC2 instances.

Architecture:

```text
ECS
 ↓
Capacity Provider
 ↓
Auto Scaling Group
 ↓
EC2 Instances
```

---

# Why Use EC2 Capacity Providers?

Benefits:

- Lower cost
- Full control
- GPU support
- Custom AMIs

---

# EC2 Capacity Provider Auto Scaling

Capacity Providers can scale:

```text
EC2 Instances
```

automatically.

Example:

```text
Need More Tasks
       ↓
Need More Capacity
       ↓
Launch EC2 Instances
```

---

# Fargate Capacity Provider

Uses:

```text
AWS Managed Infrastructure
```

No EC2 management required.

---

Architecture

```text
ECS
 ↓
Fargate Capacity Provider
 ↓
Fargate Tasks
```

---

# Advantages

- No server management
- Fast deployment
- Simpler operations

---

# Fargate Spot

Uses spare AWS capacity.

Similar to:

```text
EC2 Spot
```

but for Fargate.

---

# Cost Benefits

Savings:

```text
Up To 70%
```

compared to standard Fargate.

---

# Important Limitation

AWS may reclaim capacity.

Tasks can be interrupted.

---

# Fargate Spot Architecture

```text
ECS
 ↓
Fargate Spot
 ↓
Background Workloads
```

---

# Good Use Cases

Examples:

- ETL Jobs
- Batch Processing
- Report Generation
- Background Workers

---

# Bad Use Cases

Avoid for:

- Critical APIs
- Customer-facing systems
- Real-time applications

---

# Capacity Provider Strategy

Strategies determine how tasks are distributed.

Example:

```text
70% Fargate Spot
30% Fargate
```

---

# Why Use Strategies?

Balance:

- Cost
- Reliability
- Performance

---

# Strategy Components

Two important settings:

```text
Base
Weight
```

---

# Base

Minimum tasks assigned.

Example:

```text
Base = 2
```

First two tasks always use that provider.

---

# Weight

Controls distribution.

Example:

```text
Fargate Weight = 1
Spot Weight = 3
```

---

Distribution:

```text
25% Fargate
75% Spot
```

approximately.

---

# Example Strategy

```text
Provider        Weight

Fargate            1
Fargate Spot       4
```

Result:

Most tasks use Spot.

---

Small number use standard Fargate.

---

# Mixed Capacity Architecture

Example:

```text
Critical Tasks
       ↓
Fargate

Background Tasks
       ↓
Fargate Spot
```

Optimizes cost and reliability.

---

# High Availability Pattern

```text
Fargate
 +
Fargate Spot
```

If Spot capacity disappears:

Standard Fargate remains available.

---

# EC2 + Fargate Strategy

Example:

```text
EC2
 ↓
Base Workload

Fargate
 ↓
Traffic Spikes
```

Hybrid architecture.

---

# Capacity Provider Auto Scaling

Capacity Providers integrate with:

```text
Auto Scaling Groups
```

---

Workflow:

```text
More Tasks Needed
       ↓
More EC2 Capacity Needed
       ↓
ASG Scales Out
```

---

# Cost Optimization Example

Without Strategy:

```text
100% Fargate
```

Higher cost.

---

With Strategy:

```text
80% Spot
20% Fargate
```

Lower cost.

---

# Production Example

Video Processing Platform

Requirements:

- High throughput
- Low cost

Architecture:

```text
API Layer
 ↓
Fargate

Workers
 ↓
Fargate Spot
```

---

Benefits:

- Reliable APIs
- Cheap background processing

---

# Capacity Provider Lifecycle

```text
Service Created
       ↓
Strategy Applied
       ↓
Tasks Scheduled
       ↓
Provider Selected
```

---

# Common Capacity Provider Designs

## Cost Optimized

```text
90% Spot
10% Fargate
```

---

## Balanced

```text
70% Spot
30% Fargate
```

---

## Maximum Reliability

```text
100% Fargate
```

---

# Common Mistakes

## Using Spot for Critical APIs

Risk:

Unexpected interruptions.

---

## Ignoring Capacity Planning

Leads to:

```text
Pending Tasks
```

---

## Incorrect Weight Configuration

Causes:

Unexpected distribution.

---

## No Fallback Capacity

Risk:

Reduced availability.

---

# Troubleshooting

## Tasks Remain Pending

Check:

```text
Available Capacity
Provider Configuration
Service Events
```

---

## Spot Interruptions

Expected behavior.

Use fallback capacity.

---

## Unexpected Task Distribution

Verify:

```text
Weights
Base Values
```

---

# Common Interview Questions

## What is a Capacity Provider?

Determines where ECS tasks run.

---

## Why Use Capacity Providers?

Provides flexible workload placement.

---

## What is Fargate Spot?

Discounted spare Fargate capacity.

---

## When Should You Use Spot?

Non-critical workloads.

---

## What Are Base and Weight?

Base:

Minimum task assignment.

Weight:

Distribution ratio.

---

## Can ECS Mix Capacity Types?

Yes.

Using Capacity Provider Strategies.

---

# Senior Engineer Perspective

Capacity Providers are not just an ECS feature.

They are a cost and architecture tool.

A senior engineer considers:

- Availability
- Cost
- Performance
- Business Impact

before choosing where workloads run.

The goal is not simply:

```text
Run Containers
```

The goal is:

```text
Run Containers Efficiently
```

and at the appropriate reliability level.

---

# Key Takeaways

- Capacity Providers determine where tasks run.
- ECS supports EC2, Fargate, and Fargate Spot providers.
- Capacity Provider Strategies distribute workloads.
- Base and Weight control placement behavior.
- Fargate Spot significantly reduces costs.
- Hybrid strategies improve reliability and efficiency.
- Capacity Providers are critical for production-scale ECS environments.
