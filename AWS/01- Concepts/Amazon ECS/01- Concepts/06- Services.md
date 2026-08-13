# ECS Services

# What is an ECS Service?

An ECS Service is responsible for maintaining a specified number of running tasks.

Think of a Service as:

```text
Task Manager
```

that continuously monitors your application and ensures the desired state is maintained.

---

# Why Do We Need Services?

Without Services:

```text
Run Task
    ↓
Task Crashes
    ↓
Application Down
```

No automatic recovery.

---

With Services:

```text
Run Task
    ↓
Task Crashes
    ↓
Service Detects Failure
    ↓
Replacement Task Created
```

Application remains available.

---

# Service Architecture

```text
ECS Cluster
      ↓
ECS Service
      ↓
Tasks
```

The Service continuously monitors all running tasks.

---

# Desired State Management

This is the most important ECS Service concept.

Desired State:

```text
3 Tasks
```

Current State:

```text
3 Tasks
```

Healthy.

---

Task Failure:

```text
Desired = 3
Current = 2
```

ECS detects drift.

Action:

```text
Launch New Task
```

Final State:

```text
Desired = 3
Current = 3
```

---

# Service Scheduler

## What is the Scheduler?

The Scheduler decides:

- Where tasks run
- When tasks start
- When tasks stop
- How deployments occur
- How recovery happens

---

# Scheduler Responsibilities

## Task Placement

Selects compute resources.

Example:

```text
EC2 Instance A
EC2 Instance B
```

Scheduler determines placement.

---

## Recovery

Detects failed tasks.

Creates replacements.

---

## Deployment Management

Controls rollout process.

---

## Scaling

Adds or removes tasks.

---

# Self-Healing

Self-healing is one of ECS's biggest advantages.

Example:

```text
Task A
Task B
Task C
```

Desired Count:

```text
3
```

---

Task B Crashes

Result:

```text
Task A
Task C
```

Running Count:

```text
2
```

---

Service Action

```text
Launch Task D
```

Final State:

```text
Task A
Task C
Task D
```

Running Count:

```text
3
```

---

# Health Checks

Health checks determine whether tasks are healthy.

Two primary types:

- Container Health Checks
- Load Balancer Health Checks

---

# Container Health Checks

Executed inside the container.

Example:

```bash
curl http://localhost:8000/health
```

Healthy:

```text
200 OK
```

Unhealthy:

```text
500 Error
```

---

# ALB Health Checks

Application Load Balancer periodically checks:

```text
/health
```

If unhealthy:

```text
Remove From Rotation
```

Traffic stops flowing to that task.

---

# Health Check Workflow

```text
Task
 ↓
Health Check Fails
 ↓
Marked Unhealthy
 ↓
Service Stops Task
 ↓
Replacement Created
```

---

# Desired Count

Determines how many tasks ECS should maintain.

Example:

```text
Desired Count = 4
```

ECS always attempts to maintain:

```text
4 Running Tasks
```

---

# Service Discovery

Problem:

How do containers find each other?

Example:

```text
Order Service
Needs
Payment Service
```

IP addresses change frequently.

---

# Solution

AWS Cloud Map

Example:

```text
payment.internal
```

instead of:

```text
10.0.1.20
```

---

# Load Balancer Integration

Most production services use:

```text
Application Load Balancer
```

Architecture:

```text
Users
  ↓
ALB
  ↓
ECS Service
  ↓
Tasks
```

---

# Benefits

- High Availability
- Traffic Distribution
- Health Checks
- SSL Termination

---

# Deployment Types

ECS supports:

- Rolling Deployment
- Blue/Green Deployment

---

# Rolling Deployment

Default deployment strategy.

Version 1:

```text
Task A
Task B
Task C
```

---

Version 2 Deployment

ECS gradually replaces tasks.

```text
Task A2
Task B2
Task C2
```

---

Benefits:

- Zero downtime
- Simpler deployment

---

# Deployment Configuration

Important parameters:

## Minimum Healthy Percent

Example:

```text
100%
```

All tasks remain available.

---

## Maximum Percent

Example:

```text
200%
```

Allows temporary over-provisioning.

---

Example

Desired:

```text
4 Tasks
```

Maximum:

```text
200%
```

Temporary:

```text
8 Tasks
```

during deployment.

---

# Blue/Green Deployment

Two environments:

```text
Blue
Green
```

Blue:

Current production.

Green:

New version.

---

Traffic Switch:

```text
Blue
 ↓
Green
```

Benefits:

- Easy rollback
- Safer releases

---

# Deployment Circuit Breaker

Protects failed deployments.

Scenario:

```text
New Version
      ↓
Fails Health Checks
```

ECS:

```text
Rollback Deployment
```

Automatically.

---

# Auto Scaling Integration

Services integrate with:

```text
Application Auto Scaling
```

Example:

```text
CPU > 70%
```

Action:

```text
Add More Tasks
```

---

# Scaling Example

Initial:

```text
2 Tasks
```

Traffic Spike:

```text
CPU = 85%
```

Scaling:

```text
2 → 6 Tasks
```

---

# Failure Scenarios

## Container Crash

Handled automatically.

---

## EC2 Failure

Scheduler launches replacement elsewhere.

---

## Health Check Failure

Task removed from service.

Replacement launched.

---

## Deployment Failure

Circuit breaker rollback.

---

# Production Architecture Example

```text
Internet
    ↓
ALB
    ↓
ECS Service
    ↓
6 Tasks
    ↓
RDS
```

Features:

- Auto Scaling
- Self-Healing
- Health Checks
- Monitoring

---

# Production Best Practices

## Always Use Services

Avoid standalone tasks for APIs.

---

## Configure Health Checks

Ensure failures are detected.

---

## Enable Deployment Circuit Breakers

Automatic rollback protection.

---

## Use Auto Scaling

Handle traffic spikes.

---

## Integrate With ALB

Improve availability.

---

# Common Mistakes

## Running APIs As Standalone Tasks

No self-healing.

---

## No Health Checks

Traffic reaches failed containers.

---

## Fixed Desired Counts

Cannot handle traffic growth.

---

## Ignoring Deployment Rollbacks

Increases outage risk.

---

# Common Interview Questions

## What is an ECS Service?

A component that maintains desired task count.

---

## Difference Between Task and Service?

Task:

Single execution.

Service:

Maintains running tasks.

---

## What Happens When a Task Fails?

Service launches replacement.

---

## What is Desired State?

Target number of running tasks.

---

## Why Use Health Checks?

Detect unhealthy tasks.

---

## What is Self-Healing?

Automatic recovery from failures.

---

# Senior Engineer Perspective

Services are the foundation of production ECS workloads.

Senior engineers focus on:

- Availability
- Recovery
- Scalability
- Deployment Safety
- Monitoring

Understanding Services is critical because nearly every ECS feature builds on top of them.

---

# Key Takeaways

- ECS Services maintain desired task counts.
- Services provide self-healing.
- Health checks determine task health.
- ALBs distribute traffic.
- Deployments support rolling and blue/green strategies.
- Auto Scaling integrates directly with Services.
- Services are essential for production workloads.
