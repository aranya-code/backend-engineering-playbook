# Auto Scaling Issues

Amazon ECS Auto Scaling automatically adjusts the number of running tasks or underlying compute capacity based on application demand. When Auto Scaling does not behave as expected, applications may become overloaded, deployments may fail, or unnecessary infrastructure costs may increase.

This guide explains how to troubleshoot Service Auto Scaling, Cluster Auto Scaling, and Capacity Providers in Amazon ECS.

---

# Typical Symptoms

You may observe one or more of the following:

- Tasks never scale out.
- Tasks never scale in.
- CPU remains above 90%.
- Service becomes overloaded.
- Cluster has no available capacity.
- Scaling alarms never trigger.
- Scaling activities fail.

Example

```
Traffic Increases

↓

CPU = 95%

↓

Running Tasks = 2

↓

No Scaling
```

---

# Understanding ECS Auto Scaling

There are two different types of scaling in ECS.

## Service Auto Scaling

Scales the number of running tasks.

```
Traffic

↓

CloudWatch Metric

↓

Scaling Policy

↓

Increase Tasks
```

---

## Cluster Auto Scaling

Scales the EC2 instances that host ECS tasks.

```
Pending Tasks

↓

Capacity Provider

↓

Launch EC2 Instance

↓

Run Tasks
```

---

# Troubleshooting Workflow

```
Scaling Problem

        │

        ▼

CloudWatch Metrics

        │

        ▼

Scaling Policy

        │

        ▼

CloudWatch Alarm

        │

        ▼

Capacity Provider

        │

        ▼

Cluster Capacity

        │

        ▼

Root Cause
```

---

# Step 1: Verify Auto Scaling Is Enabled

Start by confirming that Auto Scaling is enabled.

Review:

- Minimum Capacity
- Desired Capacity
- Maximum Capacity

Example

```
Minimum

2

Desired

2

Maximum

10
```

If Auto Scaling is disabled, no scaling actions will occur.

---

# Step 2: Review CloudWatch Metrics

Verify that the scaling metric is changing.

Common metrics include:

- CPU Utilization
- Memory Utilization
- Request Count
- ALB Request Count Per Target
- Custom CloudWatch Metrics

Example

```
CPU

92%
```

If the metric never crosses the configured threshold, scaling will never occur.

---

# Step 3: Verify Scaling Policies

Common policy types include:

- Target Tracking
- Step Scaling
- Scheduled Scaling

Example

```
Target CPU

70%
```

If CPU exceeds 70%, ECS should add tasks.

---

# Step 4: Review CloudWatch Alarms

Scaling policies depend on CloudWatch alarms.

Verify:

- Alarm exists
- Alarm state
- Threshold
- Metric
- Evaluation period

Example

```
Alarm

OK

↓

ALARM
```

If the alarm never enters the **ALARM** state, scaling does not occur.

---

# Step 5: Verify Maximum Capacity

A common mistake is reaching the configured maximum task count.

Example

```
Maximum Tasks

4

Running

4
```

Even if CPU reaches 100%, ECS cannot launch additional tasks.

---

## Resolution

Increase the maximum capacity.

---

# Step 6: Verify Cluster Capacity

Service Auto Scaling only creates new tasks.

The cluster must have enough CPU and memory.

Example

```
Scale Out

↓

No EC2 Capacity

↓

Pending Tasks
```

---

## Investigation

Check:

- Available CPU
- Available Memory
- Running Tasks
- EC2 Instances

---

# Step 7: Review Capacity Providers

Capacity Providers manage EC2 infrastructure.

Verify:

- Managed Scaling enabled
- Managed Termination Protection
- Target Capacity
- Scaling status

If Capacity Providers are misconfigured, Cluster Auto Scaling may never launch additional instances.

---

# Step 8: Verify Pending Tasks

If tasks remain pending after scaling:

Review:

- CPU
- Memory
- ENIs
- Placement Constraints
- Subnet IP availability

Pending tasks usually indicate insufficient infrastructure.

---

# Step 9: Review Scaling Activities

Review the ECS Service scaling history.

Example

```
Scale Out

Succeeded
```

or

```
Scale Out

Failed
```

Scaling history often provides the exact failure reason.

---

# Step 10: Verify Application Metrics

Sometimes Auto Scaling appears broken because the wrong metric is being used.

Poor metrics include:

- Average CPU for I/O-bound workloads
- Memory for bursty traffic

Better metrics might include:

- Request Count
- Queue Length
- Response Time
- Custom Business Metrics

---

# Common Auto Scaling Problems

## Tasks Never Scale Out

Possible causes

- Auto Scaling disabled
- CloudWatch Alarm never triggered
- Maximum capacity reached
- Cluster lacks capacity
- Capacity Provider disabled

---

## Tasks Never Scale In

Possible causes

- Minimum capacity too high
- Cooldown period active
- Metric remains above threshold

---

## Tasks Scale Too Frequently

Example

```
Scale Out

↓

Scale In

↓

Scale Out

↓

Scale In
```

This is called **scaling oscillation** or **thrashing**.

---

## Resolution

Increase:

- Cooldown period
- Evaluation period

Use Target Tracking instead of aggressive Step Scaling when appropriate.

---

## High CPU But No Scaling

Possible causes

- Wrong metric
- Alarm configuration
- Maximum capacity reached
- Scaling policy disabled

---

## Pending Tasks After Scale-Out

Possible causes

- Cluster full
- No available EC2 instances
- Capacity Provider issue
- CPU exhausted
- Memory exhausted

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Auto Scaling disabled | Enable Service Auto Scaling |
| Alarm never triggered | Review CloudWatch Alarm |
| Wrong metric | Select a better scaling metric |
| Maximum capacity reached | Increase maximum task count |
| Cluster lacks capacity | Enable Cluster Auto Scaling |
| Capacity Provider disabled | Configure Managed Scaling |
| Pending tasks | Increase infrastructure capacity |
| Scaling thrashing | Increase cooldown period |

---

# Diagnostic Checklist

Before modifying scaling policies, verify:

- Auto Scaling enabled.
- CloudWatch metric correct.
- Alarm triggered.
- Scaling policy attached.
- Maximum capacity sufficient.
- Cluster has available CPU.
- Cluster has available memory.
- Capacity Provider configured.
- Scaling activity reviewed.
- Pending tasks investigated.

---

# Best Practices

- Use Target Tracking for most workloads.
- Scale on business metrics when appropriate.
- Enable Cluster Auto Scaling.
- Configure reasonable cooldown periods.
- Avoid CPU-only scaling for every application.
- Monitor scaling activities regularly.
- Configure CloudWatch dashboards.
- Test scaling under load before production deployment.

---

# Interview Questions

### What is the difference between Service Auto Scaling and Cluster Auto Scaling?

| Service Auto Scaling | Cluster Auto Scaling |
|----------------------|----------------------|
| Adds or removes tasks | Adds or removes EC2 instances |
| Uses CloudWatch metrics | Uses Capacity Providers |
| Scales applications | Scales infrastructure |

---

### Why would Auto Scaling fail to add new tasks?

Possible reasons include:

- CloudWatch Alarm not triggered
- Maximum capacity reached
- No available cluster resources
- Capacity Provider misconfiguration
- Scaling policy disabled

---

### Why do tasks remain pending after Auto Scaling?

Because Service Auto Scaling only requests new tasks.

If the cluster lacks CPU, memory, ENIs, or EC2 instances, the scheduler cannot place them.

---

### Which scaling policy is recommended for most workloads?

**Target Tracking Scaling** is generally recommended because it automatically maintains a target utilization level and requires less manual tuning than Step Scaling.

---

### What is scaling thrashing?

Scaling thrashing occurs when ECS repeatedly scales out and scales in within a short period due to aggressive thresholds or insufficient cooldown periods.

---

# Key Takeaways

- ECS uses **Service Auto Scaling** to adjust task count and **Cluster Auto Scaling** to adjust infrastructure capacity.
- CloudWatch metrics, alarms, and scaling policies work together to trigger scaling actions.
- Pending tasks after a scale-out event usually indicate insufficient cluster resources rather than a scaling policy problem.
- Choosing appropriate scaling metrics and cooldown periods helps maintain application performance while avoiding unnecessary infrastructure costs.
- Regularly monitoring scaling activities and testing scaling behavior under load improves the reliability of production ECS deployments.