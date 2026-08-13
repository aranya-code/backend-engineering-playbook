# Tasks Stuck in Pending

An Amazon ECS task enters the **PENDING** state after it has been accepted by the ECS scheduler but before it starts running. If a task remains in the **PENDING** state for an extended period, ECS is unable to allocate the required resources or complete the initialization process.

This is one of the most common production issues and is usually caused by insufficient compute resources, networking problems, placement constraints, or service configuration errors.

---

# Typical Symptoms

You may observe one or more of the following:

- Tasks remain in **PENDING** indefinitely.
- ECS Service never reaches the desired task count.
- Deployments remain in progress.
- No application logs appear.
- Load Balancer has no healthy targets.

Example

```
Desired Tasks = 4

Running = 2

Pending = 2
```

---

# Troubleshooting Workflow

Follow this troubleshooting sequence.

```
Task Pending

      │

      ▼

ECS Service Events

      │

      ▼

Cluster Capacity

      │

      ▼

CPU & Memory

      │

      ▼

Networking

      │

      ▼

Placement Constraints

      │

      ▼

Capacity Provider

      │

      ▼

Root Cause
```

---

# Step 1: Check ECS Service Events

Always begin with the ECS Service Events.

Common messages include:

```
RESOURCE:MEMORY
```

```
RESOURCE:CPU
```

```
RESOURCE:ENI
```

```
RESOURCE:PORTS
```

```
No Container Instance Found
```

These messages usually identify the missing resource.

---

# Step 2: Verify Cluster Capacity

For the EC2 launch type, ensure your cluster has sufficient compute resources.

Review:

- Available EC2 instances
- CPU availability
- Memory availability
- Running tasks
- Container instance status

Example

```
Cluster

CPU Available

0

↓

Task Cannot Start
```

---

# Step 3: Check CPU Allocation

Each task requires CPU resources.

Example

```
Task Definition

CPU = 2048

Available CPU = 1024
```

The scheduler cannot place the task.

---

## Resolution

- Reduce CPU allocation.
- Add additional EC2 instances.
- Enable Cluster Auto Scaling.

---

# Step 4: Check Memory Allocation

Memory shortages are another common cause.

Example

```
Task

Memory = 4096 MB

Cluster Available

2048 MB
```

The task remains pending until enough memory becomes available.

---

## Resolution

- Increase cluster capacity.
- Reduce task memory.
- Stop unused services.

---

# Step 5: Verify Capacity Providers

Capacity Providers determine where ECS schedules tasks.

Possible issues include:

- Disabled Capacity Provider
- Wrong Capacity Provider
- Insufficient managed capacity
- Spot capacity unavailable

---

## Investigation

Verify:

- Default Capacity Provider
- Capacity Provider strategy
- Managed scaling status

---

# Step 6: Check Placement Constraints

Placement constraints may prevent ECS from finding a suitable instance.

Example

```
attribute:instance-type

=

m6i.large
```

If no matching instance exists, tasks remain pending.

---

## Resolution

- Remove unnecessary constraints.
- Add matching EC2 instances.

---

# Step 7: Verify Placement Strategies

Common strategies include:

- Spread
- Binpack
- Random

A restrictive placement strategy combined with insufficient resources may prevent scheduling.

---

# Step 8: Check ENI Availability

When using **awsvpc** networking, every task requires an Elastic Network Interface (ENI).

Example

```
Available ENIs

0

↓

Task Pending
```

---

## Investigation

Check:

- EC2 ENI limits
- Instance type
- Running tasks
- Available network interfaces

---

## Resolution

- Upgrade instance type.
- Add more EC2 instances.
- Distribute tasks across multiple instances.

---

# Step 9: Verify Subnet IP Availability

Every task also requires an available IP address.

Example

```
Subnet

10.0.1.0/28

Available IPs

0
```

---

## Resolution

- Expand subnet.
- Create additional subnets.
- Remove unused resources.

---

# Step 10: Review Security Groups

Although Security Groups rarely keep a task in **PENDING**, incorrect networking configuration may prevent initialization.

Verify:

- Outbound rules
- VPC configuration
- NAT Gateway
- Route tables

---

# Step 11: Check IAM Permissions

Missing permissions may prevent ECS from initializing required resources.

Common examples:

```
AccessDeniedException
```

```
UnauthorizedOperation
```

Verify:

- Execution Role
- Task Role
- ECS Service Role

---

# Step 12: Verify Image Availability

If ECS cannot download the image, initialization may never complete.

Check:

- Repository exists
- Image tag
- ECR permissions
- Network connectivity

---

# Common Root Causes

| Problem | Typical Solution |
|----------|------------------|
| CPU exhausted | Add capacity or reduce CPU allocation |
| Memory exhausted | Increase memory or reduce usage |
| No EC2 instances | Launch additional instances |
| ENI exhausted | Upgrade instance type or scale out |
| No subnet IPs | Expand subnet capacity |
| Placement constraints | Relax constraints or add matching instances |
| Capacity Provider issue | Correct provider configuration |
| Image unavailable | Verify ECR image and permissions |

---

# Diagnostic Checklist

Before making changes, verify:

- ECS Service Events reviewed.
- Cluster has available CPU.
- Cluster has available memory.
- EC2 instances are healthy.
- Capacity Provider configured correctly.
- Placement constraints are valid.
- Subnets have available IP addresses.
- ENIs are available.
- Docker image exists.
- IAM permissions are correct.
- Networking is configured correctly.

---

# Best Practices

- Enable Cluster Auto Scaling.
- Monitor CPU and memory utilization.
- Monitor ENI usage.
- Use larger subnets for production workloads.
- Avoid overly restrictive placement constraints.
- Configure CloudWatch alarms for cluster capacity.
- Right-size task CPU and memory allocations.
- Regularly review cluster utilization.

---

# Interview Questions

### Why do ECS tasks remain in the PENDING state?

Common reasons include:

- Insufficient CPU
- Insufficient memory
- No EC2 capacity
- ENI exhaustion
- No available subnet IPs
- Placement constraints
- Capacity Provider issues

---

### Where would you investigate first?

A good troubleshooting sequence is:

1. ECS Service Events
2. Cluster Capacity
3. CPU & Memory
4. Capacity Providers
5. Networking
6. Placement Constraints
7. IAM Permissions

---

### Does a PENDING task mean the application is broken?

No.

A **PENDING** task indicates that ECS has not yet been able to schedule or initialize the task. In many cases, the application code has not even started running.

---

# Key Takeaways

- Tasks remain in the **PENDING** state when ECS cannot allocate the resources required to start them.
- ECS Service Events are the best starting point for identifying scheduling failures.
- CPU, memory, ENIs, subnet IP exhaustion, and Capacity Provider configuration are the most common causes.
- Regular capacity monitoring and Cluster Auto Scaling help prevent scheduling failures in production.
- Understanding the ECS scheduler and resource allocation process makes troubleshooting **PENDING** tasks much faster.