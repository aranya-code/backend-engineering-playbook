# ECS Launch Types

# What Are ECS Launch Types?

A Launch Type determines where ECS tasks run.

ECS supports two primary launch types:

```text
1. EC2 Launch Type
2. Fargate Launch Type
```

Think of launch types as the compute layer beneath ECS.

---

# High-Level Comparison

```text
ECS
 ↓
Launch Type
 ↓
Containers
```

Options:

```text
EC2
or
Fargate
```

Both run containers.

The difference is who manages the infrastructure.

---

# EC2 Launch Type

## What Is EC2 Launch Type?

With EC2 Launch Type, containers run on EC2 instances that you manage.

Architecture:

```text
ECS
 ↓
EC2 Instances
 ↓
Docker
 ↓
Containers
```

---

## Responsibilities

AWS Manages:

- ECS Control Plane
- Scheduling
- Service Management

You Manage:

- EC2 Instances
- OS Updates
- Capacity Planning
- Scaling Infrastructure
- Security Hardening

---

# EC2 Launch Type Architecture

```text
ECS Cluster
       ↓
EC2 Instance A
       ↓
Containers

EC2 Instance B
       ↓
Containers
```

Multiple containers can share the same EC2 host.

---

# Advantages of EC2 Launch Type

## Lower Cost

For long-running workloads.

Example:

```text
10 APIs
Running 24x7
```

EC2 is usually cheaper than Fargate.

---

## Full Infrastructure Control

You can:

```bash
ssh ec2-instance
```

Useful for:

- Debugging
- Custom software
- Monitoring agents

---

## GPU Support

Supported workloads:

- Machine Learning
- AI Inference
- Video Processing

---

## Custom AMIs

Organizations can create hardened images.

Example:

```text
Company AMI
 ↓
Security Tools
 ↓
Monitoring Agents
```

---

# Disadvantages of EC2 Launch Type

## Infrastructure Management

You must manage:

- Operating Systems
- Security Patches
- Capacity Planning

---

## Operational Overhead

More moving parts.

More maintenance.

---

## Capacity Risk

Insufficient capacity:

```text
Need 10 Tasks
Only Capacity For 5
```

Tasks remain pending.

---

# Fargate Launch Type

## What Is Fargate?

Fargate is AWS's serverless container platform.

Architecture:

```text
Container
     ↓
Fargate
     ↓
AWS Managed Infrastructure
```

No EC2 instances required.

---

# Fargate Responsibilities

AWS Manages:

- Servers
- OS Updates
- Scaling Infrastructure
- Security Patching

You Manage:

- Containers
- Applications
- Task Definitions

---

# Fargate Architecture

```text
ECS Cluster
       ↓
Fargate Tasks
       ↓
Containers
```

Infrastructure is completely abstracted.

---

# Advantages of Fargate

## Simplicity

No server management.

---

## Faster Deployment

Teams focus on applications.

Not infrastructure.

---

## Better Security Isolation

Each task gets:

- Dedicated networking
- Strong isolation

---

## Reduced Operational Burden

No patching.

No host maintenance.

---

# Disadvantages of Fargate

## Higher Cost

Generally more expensive.

Especially:

```text
Long Running Workloads
```

---

## Limited Host Access

Cannot SSH into infrastructure.

---

## Limited Customization

No control over underlying hosts.

---

# Resource Allocation

## EC2

Resources shared.

Example:

```text
EC2 Instance
16 vCPU
32 GB RAM
```

Multiple tasks share capacity.

---

## Fargate

Resources allocated per task.

Example:

```text
Task
2 vCPU
4 GB RAM
```

Dedicated allocation.

---

# Billing Model

## EC2 Billing

Pay for:

```text
EC2 Instance
```

Whether containers use resources or not.

---

## Fargate Billing

Pay for:

```text
CPU
Memory
Runtime
```

Per task.

---

# Cost Example

Scenario:

```text
5 APIs
24x7
```

Usually:

```text
EC2
Cheaper
```

---

Scenario:

```text
Occasional Workloads
```

Usually:

```text
Fargate
More Efficient
```

---

# Security Comparison

## EC2

Security responsibility:

- Host OS
- Patching
- SSH Access

---

## Fargate

AWS manages:

- Host Security
- OS Maintenance

Less attack surface.

---

# Performance Comparison

## EC2

Better for:

- High throughput
- Large workloads
- Specialized hardware

---

## Fargate

Better for:

- Simplicity
- Rapid deployment
- Small teams

---

# Production Use Cases

## Use EC2 When

- High traffic systems
- GPU workloads
- Cost optimization matters
- Infrastructure customization needed

Example:

```text
Large Scale API Platform
```

---

## Use Fargate When

- Small DevOps team
- Microservices
- Event-driven workloads
- Startup environments

Example:

```text
FastAPI APIs
Background Workers
```

---

# Fargate Spot

AWS provides:

```text
Unused Capacity
```

At lower cost.

Savings:

```text
Up to 70%
```

---

## Good Use Cases

- ETL Jobs
- Batch Processing
- Background Workers

---

## Avoid For

- Critical APIs
- Customer-facing services

AWS may terminate capacity.

---

# Decision Matrix

| Requirement | EC2 | Fargate |
|------------|------|---------|
| Lowest Cost | ✅ | ❌ |
| Simplicity | ❌ | ✅ |
| SSH Access | ✅ | ❌ |
| GPU Support | ✅ | ❌ |
| Serverless | ❌ | ✅ |
| Operational Ease | ❌ | ✅ |

---

# Common Interview Questions

## Which Is Cheaper?

Depends.

Long-running workloads:

```text
EC2
```

Often cheaper.

---

## Which Is Easier To Operate?

```text
Fargate
```

AWS manages infrastructure.

---

## Why Would You Choose EC2?

- Cost optimization
- GPU workloads
- Infrastructure control

---

## Why Would You Choose Fargate?

- Simplicity
- Reduced operations
- Faster deployment

---

# Common Mistakes

## Using Fargate For Everything

Can increase costs significantly.

---

## Ignoring Capacity Planning On EC2

Leads to pending tasks.

---

## Choosing EC2 Without Operational Expertise

Creates maintenance burden.

---

# Senior Engineer Perspective

Launch type selection is not a technical decision alone.

Consider:

- Cost
- Team size
- Operational maturity
- Security requirements
- Workload characteristics

A senior engineer balances these factors rather than blindly choosing the newest technology.

---

# Key Takeaways

- ECS supports EC2 and Fargate launch types.
- EC2 offers control and lower cost.
- Fargate offers simplicity and reduced operations.
- EC2 requires capacity management.
- Fargate is fully managed.
- Choose based on workload requirements and business constraints.
