# Auto Scaling Groups (ASG)

## What is an Auto Scaling Group?

An Auto Scaling Group (ASG) automatically manages EC2 instances based on application demand.

It helps applications:
- Scale out during high traffic
- Scale in during low traffic
- Maintain availability
- Replace unhealthy instances automatically

---

# Goals of ASG

## Scale Out
Adds EC2 instances when load increases.

## Scale In
Removes EC2 instances when load decreases.

## Maintain Desired Capacity
Ensures a minimum and maximum number of instances remain available.

## Automatic Recovery
Replaces unhealthy EC2 instances automatically.

## ELB Integration
New instances can automatically register with a load balancer.

---

# Important ASG Components

## Launch Template

Modern ASGs use Launch Templates instead of older Launch Configurations.

### A Launch Template Can Contain

- AMI ID
- Instance type
- User data scripts
- EBS volume configuration
- Security groups
- SSH key pair
- IAM role
- Subnet configuration
- Load balancer configuration

---

# ASG Capacity Settings

## Minimum Capacity
Lowest number of instances allowed.

## Maximum Capacity
Highest number of instances allowed.

## Desired Capacity
Target number of running instances.

---

# Scaling Policies

## Dynamic Scaling

Automatically adjusts capacity based on metrics.

### Common Metrics
- CPU Utilization
- Request Count Per Target
- Network Traffic
- Memory Utilization (custom metric)

---

# Scaling Policy Types

## 1. Target Tracking Scaling

ASG automatically adjusts capacity to maintain a target metric.

### Example
Maintain CPU utilization around 50%.

This is the most commonly used scaling policy.

---

## 2. Simple Scaling

Performs a single scaling action based on an alarm.

Example:
- Add 1 instance when CPU > 70%

---

## 3. Step Scaling

Scales differently based on alarm severity.

Example:
- CPU > 70% → Add 1 instance
- CPU > 85% → Add 3 instances

---

# Cooldown Period

## Definition

After a scaling activity, ASG waits before launching another scaling action.

## Default Cooldown
- 300 seconds

## Purpose

Allows:
- Metrics to stabilize
- Instances to initialize properly

---

# Best Practices

## Use Ready-to-Use AMIs
This reduces startup time during scaling.

## Enable Health Checks
Use ELB health checks together with EC2 health checks.

## Use Multiple Availability Zones
Improves high availability.

## Monitor Through CloudWatch
Track scaling behavior and application health.

---

# Interview Notes

## Common Questions

### What happens if an EC2 instance becomes unhealthy?
ASG terminates and replaces it automatically.

### Difference Between Desired, Minimum, and Maximum Capacity?
- Minimum = lower limit
- Maximum = upper limit
- Desired = target running instances

### Which scaling policy is most commonly used?
Target Tracking Scaling.

