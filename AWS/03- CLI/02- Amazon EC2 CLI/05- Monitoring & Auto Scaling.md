# Monitoring & Auto Scaling

> Learn how to monitor Amazon EC2 instances using Amazon CloudWatch and automatically adjust compute capacity using Auto Scaling Groups (ASGs). This chapter covers metrics, alarms, launch templates, scaling policies, and production monitoring best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Monitor EC2 instances using CloudWatch
- View EC2 metrics
- Create CloudWatch alarms
- Understand Launch Templates
- Manage Auto Scaling Groups
- Configure scaling policies
- Perform instance health checks
- Optimize costs using Auto Scaling
- Implement production monitoring strategies

---

# Why Monitoring Matters

Launching an EC2 instance is only the beginning.

Production systems require continuous monitoring to:

- Detect failures
- Measure performance
- Reduce downtime
- Scale automatically
- Optimize costs

Amazon CloudWatch provides native monitoring for EC2.

---

# Monitoring Architecture

```text
EC2 Instance
      │
      ▼
CloudWatch Metrics
      │
      ▼
CloudWatch Alarm
      │
      ▼
Auto Scaling Policy
      │
      ▼
Launch / Terminate Instance
```

CloudWatch continuously collects metrics, while Auto Scaling reacts to changes.

---

# Understanding CloudWatch Metrics

Amazon EC2 automatically publishes metrics to CloudWatch.

Common metrics include:

- CPU Utilization
- Network In
- Network Out
- Disk Read Bytes
- Disk Write Bytes
- Status Check Failed

---

# Viewing Available Metrics

```bash
aws cloudwatch list-metrics \
--namespace AWS/EC2
```

Returns every available EC2 metric.

---

# Viewing CPU Utilization

```bash
aws cloudwatch get-metric-statistics \
--namespace AWS/EC2 \
--metric-name CPUUtilization \
--dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
--statistics Average \
--period 300 \
--start-time 2026-07-01T00:00:00Z \
--end-time 2026-07-02T00:00:00Z
```

This retrieves CPU usage statistics.

---

# Understanding EC2 Status Checks

Amazon EC2 performs two automatic health checks.

## System Status Check

Checks AWS infrastructure.

Examples:

- Host failure
- Hardware issue
- Power failure

---

## Instance Status Check

Checks the operating system.

Examples:

- Kernel panic
- Network configuration
- Boot failure

---

# View Instance Status

```bash
aws ec2 describe-instance-status
```

Returns:

- Instance State
- System Status
- Instance Status
- Scheduled Events

---

# CloudWatch Alarms

CloudWatch Alarms monitor metrics and perform actions.

Example:

```text
CPU > 80%

↓

Alarm Triggered

↓

Auto Scaling

↓

Launch New Instance
```

---

# Creating a CPU Alarm

```bash
aws cloudwatch put-metric-alarm \
--alarm-name HighCPU \
--metric-name CPUUtilization \
--namespace AWS/EC2 \
--statistic Average \
--period 300 \
--threshold 80 \
--comparison-operator GreaterThanThreshold \
--evaluation-periods 2
```

This alarm triggers when CPU usage exceeds 80%.

---

# Viewing Alarms

```bash
aws cloudwatch describe-alarms
```

---

# Deleting an Alarm

```bash
aws cloudwatch delete-alarms \
--alarm-names HighCPU
```

---

# Understanding Auto Scaling

Auto Scaling automatically adjusts EC2 capacity.

Benefits:

- High Availability
- Cost Optimization
- Fault Tolerance
- Elastic Capacity

---

# Auto Scaling Architecture

```text
CloudWatch Alarm
        │
        ▼
Scaling Policy
        │
        ▼
Auto Scaling Group
        │
        ▼
Launch Template
        │
        ▼
EC2 Instances
```

---

# Launch Templates

Launch Templates define how Auto Scaling launches new instances.

A Launch Template contains:

- AMI
- Instance Type
- Security Groups
- Key Pair
- IAM Role
- User Data

---

# List Launch Templates

```bash
aws ec2 describe-launch-templates
```

---

# View a Launch Template

```bash
aws ec2 describe-launch-template-versions \
--launch-template-name backend-template
```

---

# Auto Scaling Groups

An Auto Scaling Group (ASG) manages a collection of EC2 instances.

Properties include:

- Minimum Capacity
- Desired Capacity
- Maximum Capacity

Example:

```text
Minimum : 2

Desired : 4

Maximum : 10
```

---

# View Auto Scaling Groups

```bash
aws autoscaling describe-auto-scaling-groups
```

---

# View Scaling Activities

```bash
aws autoscaling describe-scaling-activities
```

Useful for troubleshooting scaling events.

---

# Scaling Policies

Scaling policies determine when Auto Scaling reacts.

Types include:

- Target Tracking
- Step Scaling
- Simple Scaling

Target Tracking is recommended for most workloads.

---

# Target Tracking Example

Goal:

```text
Maintain CPU Utilization

↓

50%
```

Auto Scaling automatically launches or terminates instances to maintain this target.

---

# Instance Health Checks

Auto Scaling continuously evaluates instance health.

If an instance becomes unhealthy:

```text
Unhealthy Instance

↓

Terminate

↓

Launch Replacement
```

No manual intervention is required.

---

# Scheduled Scaling

Scale infrastructure based on predictable demand.

Examples:

- Business hours
- Black Friday
- Product launches
- Batch processing

---

# Cost Optimization

Auto Scaling reduces costs by:

- Removing idle instances
- Launching capacity only when needed
- Preventing over-provisioning

Always configure:

- Minimum Capacity
- Maximum Capacity
- Desired Capacity

carefully.

---

# Production Monitoring Workflow

```text
EC2 Instance
      │
      ▼
CloudWatch Metrics
      │
      ▼
Alarm
      │
      ▼
Scaling Policy
      │
      ▼
Launch Template
      │
      ▼
New EC2 Instance
```

---

# Common Problems

## High CPU

Possible causes:

- Application bottleneck
- Memory pressure
- High traffic

Investigate before increasing instance size.

---

## Alarm Never Triggers

Verify:

- Metric Namespace
- Evaluation Period
- Threshold
- Metric Dimensions

---

## Auto Scaling Doesn't Launch Instances

Check:

- Launch Template
- Subnet Capacity
- IAM Permissions
- Scaling Policy
- Maximum Capacity

---

# Production Best Practices

- Enable detailed CloudWatch monitoring.
- Create alarms for critical metrics.
- Use Launch Templates instead of Launch Configurations.
- Use Target Tracking Scaling.
- Monitor scaling activities.
- Review CloudWatch dashboards regularly.
- Test scaling policies before production deployment.
- Avoid over-scaling by setting realistic thresholds.

---

# Real-World Workflow

Deploying a production web application.

```text
Launch Template
        │
        ▼
Auto Scaling Group
        │
        ▼
CloudWatch Monitoring
        │
        ▼
Traffic Increase
        │
        ▼
CPU > 70%
        │
        ▼
Launch Additional Instance
        │
        ▼
Load Balancer
```

---

# Architecture Note

```text
Users
      │
      ▼
Application Load Balancer
      │
      ▼
Auto Scaling Group
      │
      ▼
EC2 Instances
      │
      ▼
CloudWatch Metrics
      │
      ▼
CloudWatch Alarms
      │
      └──────────────┐
                     ▼
              Scaling Policy
```

CloudWatch continuously feeds metrics into Auto Scaling, enabling automatic capacity adjustments based on demand.

---

# Interview Note

### Question

**What is the difference between CloudWatch and Auto Scaling?**

### Answer

Amazon **CloudWatch** is a monitoring service that collects metrics, logs, and events from AWS resources such as EC2 instances. It provides visibility into system health and performance. **Auto Scaling** uses those metrics—often through CloudWatch alarms—to automatically adjust the number of EC2 instances based on demand. In short, CloudWatch observes the system, while Auto Scaling acts on that information to maintain availability and optimize costs.

---

# Key Takeaways

- CloudWatch provides monitoring for EC2 instances.
- CloudWatch Alarms react to metric thresholds.
- Auto Scaling Groups maintain application availability.
- Launch Templates define how new EC2 instances are created.
- Target Tracking Scaling is recommended for most production workloads.
- Health checks automatically replace unhealthy instances.
- Monitoring and Auto Scaling together improve reliability, scalability, and cost efficiency.

---
