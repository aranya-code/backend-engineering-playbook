# 07- Elastic Beanstalk Auto Scaling

---

# Introduction

One of the biggest advantages of cloud computing is the ability to automatically adjust infrastructure capacity based on demand.

Without Auto Scaling:

```text
Traffic Increase
       ↓
Server Overload
       ↓
Slow Response
       ↓
Application Failure
```

With Auto Scaling:

```text
Traffic Increase
       ↓
New Instances Created
       ↓
Traffic Distributed
       ↓
Application Remains Healthy
```

Elastic Beanstalk integrates directly with AWS Auto Scaling to automatically increase or decrease capacity based on workload.

---

# What Is Auto Scaling?

Auto Scaling is the process of automatically adjusting the number of EC2 instances in an environment.

The objective is:

```text
Right Capacity
At The Right Time
At The Lowest Cost
```

---

# Why Auto Scaling Matters

Applications rarely receive constant traffic.

Example:

```text
9 AM  -> 100 Users
12 PM -> 1,000 Users
2 AM  -> 20 Users
```

Provisioning for peak traffic all the time results in:

```text
Wasted Infrastructure
Higher Costs
```

Auto Scaling solves this problem.

---

# Auto Scaling Architecture

```text
Users
  ↓
ALB
  ↓
Auto Scaling Group
  ↓
EC2 Instances
```

Elastic Beanstalk automatically creates and manages the Auto Scaling Group.

---

# Auto Scaling Components

Elastic Beanstalk Auto Scaling relies on:

```text
Auto Scaling Group
Launch Configuration
CloudWatch Metrics
Scaling Policies
EC2 Instances
```

---

# Auto Scaling Workflow

```text
CloudWatch Metric
        ↓
Threshold Reached
        ↓
Scaling Policy Triggered
        ↓
Auto Scaling Group
        ↓
Launch Or Terminate Instance
```

---

# Desired Capacity

Desired Capacity determines how many instances should be running.

Example:

```text
Desired Capacity = 3
```

Result:

```text
EC2-1
EC2-2
EC2-3
```

If one instance fails:

```text
EC2-1
EC2-2
X EC2-3
```

Auto Scaling launches a replacement automatically.

---

# Minimum Capacity

Defines the minimum number of instances.

Example:

```text
Minimum Capacity = 2
```

Elastic Beanstalk never scales below:

```text
2 Instances
```

---

# Maximum Capacity

Defines the maximum number of instances.

Example:

```text
Maximum Capacity = 10
```

Elastic Beanstalk will never launch more than:

```text
10 Instances
```

---

# Example Configuration

```text
Minimum = 2
Desired = 4
Maximum = 10
```

Normal operation:

```text
4 Instances
```

Scale Out:

```text
5
6
7
...
10
```

Scale In:

```text
9
8
7
...
2
```

---

# Scaling Policies

Scaling policies define when scaling actions occur.

Common policy types:

```text
Target Tracking
Step Scaling
Scheduled Scaling
Predictive Scaling
```

---

# Target Tracking Scaling

Most commonly used.

Goal:

```text
Maintain Target Metric
```

Example:

```text
CPU Utilization = 50%
```

---

# Target Tracking Example

```text
Current CPU = 80%
Target CPU = 50%
```

Result:

```text
Launch Additional Instances
```

---

# Benefits

```text
Simple
Automatic
Recommended By AWS
```

---

# Step Scaling

Uses multiple thresholds.

Example:

```text
CPU > 60%
Scale +1

CPU > 80%
Scale +2

CPU > 90%
Scale +3
```

---

# Step Scaling Workflow

```text
Metric
  ↓
Threshold
  ↓
Scaling Action
```

Provides more control than Target Tracking.

---

# Scheduled Scaling

Used when traffic patterns are predictable.

Example:

```text
Business Hours
9 AM - 6 PM
```

---

# Scheduled Scaling Example

Scale Out:

```text
9 AM
Desired Capacity = 6
```

Scale In:

```text
10 PM
Desired Capacity = 2
```

---

# Benefits

```text
Predictable
Cost Effective
Simple
```

---

# Predictive Scaling

AWS analyzes historical patterns.

Example:

```text
Traffic Always Increases
Every Monday Morning
```

AWS prepares capacity before demand occurs.

---

# Scale Out

Scale Out means:

```text
Add More Instances
```

Example:

Before:

```text
Instance-1
Instance-2
```

After:

```text
Instance-1
Instance-2
Instance-3
Instance-4
```

---

# Scale In

Scale In means:

```text
Remove Instances
```

Example:

Before:

```text
Instance-1
Instance-2
Instance-3
Instance-4
```

After:

```text
Instance-1
Instance-2
```

---

# Scale Up vs Scale Out

Scale Up:

```text
Bigger Server
```

Example:

```text
t3.small
   ↓
t3.large
```

---

# Scale Out

```text
More Servers
```

Example:

```text
2 Instances
    ↓
6 Instances
```

Cloud-native architectures generally prefer Scale Out.

---

# CloudWatch Metrics

Auto Scaling relies on CloudWatch.

Common metrics:

```text
CPU Utilization
Network In
Network Out
Request Count
Latency
```

---

# CPU-Based Scaling

Most common approach.

Example:

```text
CPU > 70%
```

Trigger:

```text
Scale Out
```

---

# Request Count Scaling

Useful for APIs.

Example:

```text
Requests Per Minute > Threshold
```

Trigger:

```text
Launch New Instances
```

---

# Network-Based Scaling

Useful for:

```text
Streaming
File Transfer
Large Payload APIs
```

Metrics:

```text
Network In
Network Out
```

---

# Health-Based Scaling

Elastic Beanstalk continuously monitors health.

Healthy:

```text
Green
```

Warning:

```text
Yellow
```

Critical:

```text
Red
```

---

# Instance Replacement

If an instance becomes unhealthy:

```text
Instance Failure
        ↓
Terminate Instance
        ↓
Launch New Instance
```

This improves reliability.

---

# Multi-AZ Auto Scaling

Production environments should use:

```text
Multiple Availability Zones
```

Architecture:

```text
AZ-A
 ↓
EC2

AZ-B
 ↓
EC2
```

---

# Benefits

```text
High Availability
Fault Tolerance
Disaster Resilience
```

---

# Cost Optimization

Auto Scaling helps reduce costs.

Without Auto Scaling:

```text
10 Instances Running
24 Hours
```

With Auto Scaling:

```text
2 Instances At Night
10 Instances During Peak Hours
```

Result:

```text
Lower AWS Costs
```

---

# Common Auto Scaling Mistakes

## Minimum Capacity Too Low

Example:

```text
Minimum = 1
```

Risk:

```text
Single Point Of Failure
```

---

## Maximum Capacity Too Low

Example:

```text
Maximum = 3
```

Traffic spike:

```text
Application Overloaded
```

---

## Aggressive Scaling

Example:

```text
CPU > 20%
```

Result:

```text
Constant Scaling Events
Higher Costs
```

---

## No Monitoring

Without CloudWatch:

```text
Scaling Problems Go Unnoticed
```

---

# Production Auto Scaling Example

```text
Minimum Capacity = 2
Desired Capacity = 4
Maximum Capacity = 10

Scaling Metric:
CPU Utilization

Target:
50%
```

---

# Scaling Lifecycle

```text
Traffic Increase
       ↓
CPU Increases
       ↓
CloudWatch Alarm
       ↓
Scaling Policy
       ↓
Launch Instance
       ↓
Register With ALB
       ↓
Serve Traffic
```

---

# Interview Questions

## What Is Auto Scaling?

Automatic adjustment of EC2 capacity based on demand.

---

## What Is Desired Capacity?

Number of instances Auto Scaling attempts to maintain.

---

## Difference Between Scale Out And Scale Up?

Scale Out:

```text
More Instances
```

Scale Up:

```text
Larger Instance
```

---

## Which Scaling Policy Is Most Common?

```text
Target Tracking
```

---

## What Service Triggers Auto Scaling?

```text
CloudWatch
```

---

## Why Is Auto Scaling Important?

Improves:

```text
Availability
Performance
Cost Efficiency
```

---

# Senior Engineer Perspective

Auto Scaling is not simply about handling traffic.

It is about:

```text
Availability
Reliability
Resilience
Cost Optimization
```

A well-designed Auto Scaling strategy ensures:

```text
Applications Stay Available
Costs Stay Controlled
Infrastructure Remains Healthy
```

The goal is not to scale as much as possible.

The goal is:

```text
Scale Only When Necessary
```

while maintaining a great user experience.

---

# Key Takeaways

* Elastic Beanstalk automatically integrates with Auto Scaling.
* Auto Scaling adjusts EC2 capacity based on demand.
* Minimum, Desired, and Maximum Capacity control scaling limits.
* Target Tracking is the most commonly used scaling policy.
* CloudWatch metrics drive scaling decisions.
* Auto Scaling improves availability and reduces costs.
* Multi-AZ deployments improve fault tolerance.
* Poor scaling configuration can lead to outages or unnecessary expenses.
