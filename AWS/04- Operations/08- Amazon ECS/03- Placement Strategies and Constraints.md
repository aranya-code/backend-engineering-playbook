# ECS Placement Strategies and Constraints

# Why Placement Matters

When ECS launches a task, it must decide:

```text
Which Resource
Should Run This Task?
```

This decision impacts:

- Cost
- Availability
- Performance
- Resource Utilization

---

# ECS Scheduling Process

Example:

```text
Service Needs
3 Tasks
```

ECS Scheduler evaluates:

```text
Available Capacity
Placement Strategy
Placement Constraints
```

Then places tasks.

---

# ECS Placement Architecture

```text
ECS Service
      ↓
Scheduler
      ↓
Placement Strategy
      ↓
Available Capacity
      ↓
Task Placement
```

---

# What is a Placement Strategy?

Placement Strategies control:

```text
How ECS Distributes Tasks
```

Across available resources.

---

# Available Placement Strategies

```text
Binpack
Spread
Random
```

---

# Binpack Strategy

Goal:

```text
Maximize Resource Utilization
```

ECS fills one instance before moving to the next.

---

# Example

Resources:

```text
EC2-A
EC2-B
EC2-C
```

Tasks:

```text
Task1
Task2
Task3
Task4
```

---

Binpack Result:

```text
EC2-A
 ├── Task1
 ├── Task2
 ├── Task3
 └── Task4
```

Other instances remain mostly unused.

---

# Advantages

## Cost Optimization

Fewer instances required.

---

## Better Utilization

Resources used efficiently.

---

## Reduced Infrastructure Cost

Can terminate unused hosts.

---

# Disadvantages

## Reduced Availability

If host fails:

```text
Many Tasks Lost
```

---

## Resource Contention

Tasks compete for resources.

---

# Use Cases

Examples:

- Development environments
- Cost-sensitive workloads
- Batch processing

---

# Spread Strategy

Goal:

```text
Maximize Availability
```

Distributes tasks evenly.

---

# Example

Instances:

```text
EC2-A
EC2-B
EC2-C
```

Tasks:

```text
Task1 → EC2-A
Task2 → EC2-B
Task3 → EC2-C
```

---

# Advantages

## High Availability

Failure affects fewer tasks.

---

## Better Fault Tolerance

Workloads distributed.

---

## Multi-AZ Friendly

Improves resilience.

---

# Disadvantages

## Higher Cost

More infrastructure required.

---

## Lower Resource Utilization

Some capacity remains unused.

---

# Use Cases

Examples:

- Customer-facing APIs
- Production services
- Critical systems

---

# Random Strategy

Goal:

```text
Random Placement
```

Tasks assigned randomly.

---

# Example

```text
Task1 → EC2-A
Task2 → EC2-C
Task3 → EC2-A
Task4 → EC2-B
```

---

# Advantages

Simple scheduling.

---

# Disadvantages

Unpredictable distribution.

Rarely used in production.

---

# Placement Strategy Comparison

| Strategy | Goal | Availability | Cost |
|-----------|------|-------------|------|
| Binpack | Efficiency | Lower | Lower |
| Spread | Resilience | Higher | Higher |
| Random | Simplicity | Variable | Variable |

---

# What Are Placement Constraints?

Constraints define:

```text
Where Tasks Are Allowed To Run
```

Unlike strategies:

Constraints are mandatory.

---

# Available Constraints

```text
DistinctInstance
MemberOf
```

---

# DistinctInstance Constraint

Ensures:

```text
One Task Per Instance
```

---

# Example

Without Constraint:

```text
EC2-A
 ├── Task1
 ├── Task2
```

---

With DistinctInstance:

```text
EC2-A → Task1
EC2-B → Task2
```

---

# Advantages

Improves:

- Fault Tolerance
- Availability

---

# Disadvantages

Requires:

```text
More Capacity
```

---

# Use Cases

Examples:

- Critical workloads
- Stateful applications
- High-availability systems

---

# MemberOf Constraint

Allows custom placement rules.

Example:

```text
Only Run On GPU Hosts
```

---

# Architecture

```text
GPU Nodes
 ↓
Allowed

Non-GPU Nodes
 ↓
Blocked
```

---

# Expression Example

```text
attribute:gpu == true
```

---

# Common Use Cases

Examples:

- GPU workloads
- Compliance requirements
- Dedicated hardware
- Specialized infrastructure

---

# Multi-AZ Placement

Best Practice:

Distribute tasks across:

```text
AZ-A
AZ-B
AZ-C
```

---

# Example

```text
Task1 → AZ-A
Task2 → AZ-B
Task3 → AZ-C
```

---

Benefits

- Fault tolerance
- High availability
- Disaster resilience

---

# Placement and Capacity Providers

Scheduler considers:

```text
Capacity Provider
 +
Placement Strategy
 +
Constraints
```

Before selecting a host.

---

# Scheduling Decision Example

Requirements:

```text
Spread Strategy
DistinctInstance
Fargate Provider
```

Scheduler ensures all conditions are met.

---

# Resource Optimization

Example:

```text
CPU Available
Memory Available
```

Scheduler evaluates:

```text
Can Task Fit?
```

before placement.

---

# Capacity-Aware Scheduling

Task Requirements:

```text
2 vCPU
4 GB RAM
```

---

Host Capacity:

```text
1 vCPU
2 GB RAM
```

---

Result:

```text
Placement Rejected
```

---

# GPU Workload Example

Requirements:

```text
Machine Learning Inference
```

Constraint:

```text
attribute:gpu == true
```

Scheduler places tasks only on GPU nodes.

---

# Production Example

Customer API

Requirements:

- High availability
- Multi-AZ
- Fault tolerance

Strategy:

```text
Spread
```

Constraint:

```text
DistinctInstance
```

---

Result:

Tasks distributed across hosts and zones.

---

# Cost Optimization Example

Background Processing

Requirements:

- Low cost
- High density

Strategy:

```text
Binpack
```

---

Result:

Fewer EC2 instances required.

---

# Common Mistakes

## Using Binpack for Critical APIs

Risk:

Large failure impact.

---

## Ignoring AZ Distribution

Risk:

Single AZ outage.

---

## Overusing Constraints

Risk:

Pending tasks.

---

## Insufficient Capacity

Tasks remain unscheduled.

---

# Troubleshooting

## Tasks Stuck in Pending

Check:

```text
Available Capacity
Placement Constraints
CPU Availability
Memory Availability
```

---

## Unexpected Placement

Verify:

```text
Placement Strategy
Constraint Configuration
```

---

## Uneven Distribution

Check:

```text
Spread Configuration
Capacity Availability
```

---

# Common Interview Questions

## What is a Placement Strategy?

Controls how ECS distributes tasks.

---

## Difference Between Strategy and Constraint?

Strategy:

Preferred behavior.

Constraint:

Mandatory requirement.

---

## What is Binpack?

Maximizes resource utilization.

---

## What is Spread?

Distributes tasks for high availability.

---

## What is DistinctInstance?

One task per instance.

---

## What is MemberOf?

Custom placement rules.

---

# Senior Engineer Perspective

Placement decisions directly impact:

- Cost
- Availability
- Recovery Time
- Infrastructure Efficiency

There is no universally correct strategy.

The best strategy depends on business priorities:

```text
Cost Optimization
or
High Availability
```

A senior engineer understands the trade-offs and chooses accordingly.

---

# Key Takeaways

- Placement Strategies control task distribution.
- Binpack optimizes resource usage.
- Spread improves availability.
- Random provides simple placement.
- Constraints define mandatory placement rules.
- DistinctInstance improves fault tolerance.
- MemberOf enables specialized placement.
- Placement decisions significantly impact production systems.
