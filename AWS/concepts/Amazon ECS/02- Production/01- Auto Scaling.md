# ECS Auto Scaling

# Why Auto Scaling Matters

One of the biggest advantages of cloud computing is elasticity.

Traditional infrastructure:

```text
Peak Traffic
      ↓
Buy More Servers
```

Problems:

- Expensive
- Slow
- Overprovisioned

---

Cloud-native approach:

```text
Traffic Increases
       ↓
Scale Automatically
```

Pay only for required capacity.

---

# What is ECS Auto Scaling?

ECS Auto Scaling automatically adjusts:

```text
Number of Tasks
```

based on demand.

Example:

```text
2 Tasks
```

Traffic increases.

ECS scales to:

```text
8 Tasks
```

---

# Benefits

Provides:

- High Availability
- Better Performance
- Cost Optimization
- Reduced Manual Operations

---

# Scaling Concepts

Two primary actions:

```text
Scale Out
Scale In
```

---

# Scale Out

Adds more tasks.

Example:

```text
2 Tasks
 ↓
6 Tasks
```

Used when traffic increases.

---

# Scale In

Removes unnecessary tasks.

Example:

```text
6 Tasks
 ↓
2 Tasks
```

Used when demand decreases.

---

# ECS Auto Scaling Architecture

```text
CloudWatch Metric
        ↓
Scaling Policy
        ↓
ECS Service
        ↓
Task Count Changes
```

---

# Components

ECS Auto Scaling relies on:

- ECS Service
- CloudWatch Metrics
- Scaling Policies
- Application Auto Scaling

---

# Scaling Metrics

Most common metrics:

```text
CPU Utilization
Memory Utilization
Request Count
Custom Metrics
```

---

# CPU-Based Scaling

Example:

Target:

```text
CPU = 60%
```

Current:

```text
CPU = 85%
```

Action:

```text
Launch More Tasks
```

---

# Memory-Based Scaling

Example:

Target:

```text
Memory = 70%
```

Current:

```text
Memory = 90%
```

Action:

```text
Scale Out
```

---

# Why Memory Scaling Matters

Some applications are memory intensive.

Examples:

- Java Applications
- Data Processing
- Analytics

CPU may remain low while memory becomes exhausted.

---

# Target Tracking Scaling

Most commonly used policy.

You define:

```text
Desired Metric Value
```

Example:

```text
CPU = 60%
```

---

# How It Works

If CPU exceeds target:

```text
Scale Out
```

If CPU falls below target:

```text
Scale In
```

---

# Example

Initial:

```text
2 Tasks
```

Traffic Spike:

```text
CPU = 85%
```

Result:

```text
4 Tasks
```

CPU returns to target.

---

# Advantages

- Simple
- Automatic
- Recommended by AWS

---

# Step Scaling

Provides more control.

Rules are predefined.

---

Example

```text
CPU > 70%
       ↓
Add 2 Tasks
```

---

```text
CPU > 90%
       ↓
Add 5 Tasks
```

---

Benefits

- Predictable scaling
- Fine-grained control

---

# Scheduled Scaling

Scaling based on time.

Example:

```text
Business Hours
```

Scale to:

```text
20 Tasks
```

---

Night:

```text
3 Tasks
```

---

Use Cases

- Office applications
- Batch systems
- Predictable workloads

---

# CloudWatch Metrics

CloudWatch provides scaling data.

Examples:

```text
CPUUtilization
MemoryUtilization
RequestCount
```

---

# Custom Metrics

Applications can publish metrics.

Example:

```text
Queue Length
```

---

Architecture

```text
Application
      ↓
CloudWatch Metric
      ↓
Scaling Policy
```

---

# Example Use Cases

Scale based on:

```text
Messages in SQS
```

---

Or:

```text
Pending Jobs
```

---

# Cooldown Period

Prevents rapid scaling changes.

Without cooldown:

```text
Scale Out
Scale In
Scale Out
Scale In
```

Thrashing occurs.

---

# Example

Cooldown:

```text
300 Seconds
```

Wait before next scaling event.

---

# Scaling Workflow

```text
Traffic Increase
       ↓
CPU Rises
       ↓
CloudWatch Alarm
       ↓
Scaling Policy
       ↓
Additional Tasks
```

---

# Auto Scaling with ALB

Example:

```text
Users
 ↓
ALB
 ↓
ECS Tasks
```

Traffic increases.

ALB distributes requests.

ECS launches additional tasks.

---

# Scale-In Protection

Avoid scaling too aggressively.

Bad:

```text
10 Tasks
 ↓
2 Tasks
```

immediately.

---

Good:

Gradual reduction.

Prevents performance issues.

---

# Production Example

E-commerce Platform

Normal:

```text
4 Tasks
```

---

Black Friday:

```text
40 Tasks
```

---

After Traffic Drops:

```text
4 Tasks
```

---

Fully automated.

---

# Scaling Strategies

## Conservative

Scale slowly.

Benefits:

- Lower cost

Risk:

- Slower response to spikes

---

## Aggressive

Scale rapidly.

Benefits:

- Better performance

Risk:

- Higher cost

---

# Cost Optimization

Auto Scaling reduces:

```text
Idle Resources
```

Example:

Without Scaling:

```text
20 Tasks
24x7
```

---

With Scaling:

```text
2-20 Tasks
```

Based on demand.

---

# Common Scaling Mistakes

## Scaling Only on CPU

Some applications are memory bound.

---

## No Cooldown

Causes:

```text
Thrashing
```

---

## Aggressive Scale-In

Can impact availability.

---

## Wrong Thresholds

Example:

```text
CPU > 20%
```

Unnecessary scaling.

---

# Troubleshooting

## Tasks Not Scaling

Check:

```text
CloudWatch Metrics
Scaling Policies
Service Limits
```

---

## Scaling Too Frequently

Check:

```text
Cooldown Settings
```

---

## Delayed Scaling

Check:

```text
Metric Frequency
Policy Configuration
```

---

# Common Interview Questions

## What is ECS Auto Scaling?

Automatically adjusts task count based on demand.

---

## Difference Between Scale Out and Scale In?

Scale Out:

Add tasks.

Scale In:

Remove tasks.

---

## What is Target Tracking?

Maintain a target metric value.

---

## What is Step Scaling?

Rule-based scaling.

---

## Why Use Cooldowns?

Prevent scaling thrashing.

---

## Can ECS Scale on Custom Metrics?

Yes.

Using CloudWatch custom metrics.

---

# Senior Engineer Perspective

Auto Scaling is not just about performance.

It affects:

- Availability
- User Experience
- Infrastructure Cost

The goal is not:

```text
Always Scale
```

The goal is:

```text
Scale Intelligently
```

A good scaling strategy balances performance and cost.

---

# Key Takeaways

- ECS Auto Scaling automatically adjusts task count.
- Scale Out adds tasks.
- Scale In removes tasks.
- Target Tracking is the most common policy.
- Step Scaling provides more control.
- Scheduled Scaling supports predictable workloads.
- CloudWatch metrics drive scaling decisions.
- Proper scaling improves availability and reduces cost.
