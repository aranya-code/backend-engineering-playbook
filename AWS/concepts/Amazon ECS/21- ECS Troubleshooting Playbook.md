# ECS Troubleshooting Playbook

# Introduction

Most engineers learn:

```text
How To Deploy ECS
```

Very few learn:

```text
How To Debug ECS
```

Production value comes from troubleshooting skills.

When systems fail:

```text
Customers Don't Care
How It Was Designed

Customers Care
How Fast It Is Fixed
```

---

# Golden Troubleshooting Rule

Never start with assumptions.

Start with:

```text
Facts
Metrics
Logs
Events
```

---

# ECS Troubleshooting Framework

When something breaks:

```text
1. What Changed?
2. What Failed?
3. When Did It Fail?
4. Who Is Impacted?
5. Why Did It Fail?
```

---

# Troubleshooting Layers

Think in layers.

```text
Application
Container
Task
Service
Network
Infrastructure
AWS Services
```

---

# ECS Incident Workflow

```text
Alert
 ↓
Impact Assessment
 ↓
Identify Scope
 ↓
Collect Evidence
 ↓
Root Cause
 ↓
Mitigation
 ↓
Permanent Fix
```

---

# Problem #1

## Task Stuck In PENDING

Most common ECS issue.

---

# Symptoms

```text
Desired = 5

Running = 2

Pending = 3
```

---

# Possible Causes

### Insufficient Capacity

Example:

```text
Need:
4 vCPU

Available:
2 vCPU
```

Task cannot be scheduled.

---

### Memory Exhaustion

Example:

```text
Task Requires:
8 GB

Available:
4 GB
```

---

### Capacity Provider Problems

Examples:

- Fargate capacity unavailable
- Auto Scaling Group exhausted

---

### Placement Constraints

Example:

```text
DistinctInstance
```

but insufficient instances.

---

# Investigation

Check:

```text
Service Events
Cluster Capacity
Task Events
```

---

# Problem #2

## Task Starts Then Stops

---

# Symptoms

```text
PENDING
 ↓
RUNNING
 ↓
STOPPED
```

within seconds.

---

# Common Causes

### Application Crash

Example:

```python
ImportError
```

Application exits.

---

### Missing Environment Variables

Example:

```text
DATABASE_URL Missing
```

Startup failure.

---

### Secret Retrieval Failure

Task cannot retrieve credentials.

---

### Invalid Command

Container entrypoint fails.

---

# Investigation

Check:

```text
CloudWatch Logs
Task Exit Code
Container Logs
```

---

# Problem #3

## Cannot Pull Image From ECR

---

# Symptoms

```text
CannotPullContainerError
```

---

# Common Causes

### Missing Execution Role

Task lacks:

```text
ecr:GetAuthorizationToken
```

---

### Wrong Image URI

Example:

```text
Repository Does Not Exist
```

---

### Image Deleted

Task definition references removed image.

---

### Network Problems

No access to:

```text
ECR
```

---

# Investigation

Check:

```text
Execution Role
Task Events
ECR Repository
```

---

# Problem #4

## ALB Health Check Failure

---

# Symptoms

```text
Unhealthy Targets
```

---

# Common Causes

### Wrong Health Check Path

Example:

```text
/health
```

Application serves:

```text
/healthz
```

---

### Wrong Port

ALB expects:

```text
8000
```

Application listens on:

```text
8080
```

---

### Slow Startup

Health check timeout.

---

### Application Error

Returns:

```text
500
```

---

# Investigation

Check:

```text
Target Group
Application Logs
Health Check Configuration
```

---

# Problem #5

## Service Cannot Reach Database

---

# Symptoms

```text
Connection Timeout
```

---

# Common Causes

### Security Groups

Database blocks ECS traffic.

---

### Wrong Endpoint

Incorrect hostname.

---

### DNS Issues

Service cannot resolve endpoint.

---

### Route Problems

Network path unavailable.

---

# Investigation

Verify:

```text
Security Groups
DNS Resolution
Subnet Design
```

---

# Problem #6

## Access Denied Errors

---

# Symptoms

```text
AccessDeniedException
```

---

# Common Causes

### Wrong Task Role

Missing permissions.

---

### Incorrect Resource Policy

Resource blocks access.

---

### Wrong AWS Region

Resource not found.

---

# Investigation

Check:

```text
IAM Policies
Task Role
CloudTrail
```

---

# Problem #7

## Service Not Scaling

---

# Symptoms

```text
CPU = 90%

Task Count = 2
```

No scaling occurs.

---

# Common Causes

### Missing Scaling Policy

No trigger exists.

---

### CloudWatch Metrics Missing

Scaling cannot evaluate.

---

### Cooldown Too Large

Scaling delayed.

---

### Service Limits

Account quota reached.

---

# Investigation

Check:

```text
Scaling Policy
CloudWatch
Service Events
```

---

# Problem #8

## Deployment Failure

---

# Symptoms

```text
Deployment In Progress
```

for a long time.

---

# Common Causes

### Health Check Failure

New tasks never become healthy.

---

### Startup Failure

Containers crash.

---

### Resource Constraints

New tasks cannot launch.

---

# Investigation

Review:

```text
Service Events
Target Groups
CloudWatch Logs
```

---

# Problem #9

## High CPU Usage

---

# Symptoms

```text
CPU > 90%
```

---

# Possible Causes

### Traffic Spike

Legitimate growth.

---

### Infinite Loop

Application bug.

---

### Inefficient Queries

Database bottleneck.

---

### Under-Provisioned Tasks

Insufficient CPU allocation.

---

# Investigation

Check:

```text
Application Metrics
Database Metrics
Logs
```

---

# Problem #10

## High Memory Usage

---

# Symptoms

```text
Memory > 90%
```

---

# Common Causes

### Memory Leak

Application never releases memory.

---

### Large Caches

Uncontrolled growth.

---

### Insufficient Memory

Task sizing issue.

---

# Investigation

Review:

```text
Heap Usage
Application Metrics
Container Insights
```

---

# ECS Debugging Workflow

Step 1

Check:

```text
ECS Service Events
```

---

Step 2

Check:

```text
Task Status
```

---

Step 3

Check:

```text
CloudWatch Logs
```

---

Step 4

Check:

```text
CloudWatch Metrics
```

---

Step 5

Check:

```text
Networking
```

---

Step 6

Check:

```text
IAM Permissions
```

---

# Production Incident Example

Alert:

```text
API Down
```

---

Investigation:

```text
ALB Healthy Targets = 0
```

---

Root Cause:

```text
New Deployment
Wrong Health Endpoint
```

---

Mitigation:

```text
Rollback Deployment
```

---

Resolution:

```text
Fix Configuration
Redeploy
```

---

# Root Cause Analysis (RCA)

After every incident:

Document:

```text
What Happened?
Why?
Impact?
Fix?
Prevention?
```

---

# Example RCA

Issue:

```text
Database Connectivity Failure
```

Root Cause:

```text
Security Group Change
```

Prevention:

```text
Infrastructure Review Process
```

---

# Senior Engineer Troubleshooting Checklist

Always check:

```text
Service Events
Task Events
Logs
Metrics
Health Checks
Networking
IAM
Deployments
```

before escalating.

---

# Common Interview Questions

## Task Stuck In Pending. What Do You Check?

- Capacity
- Constraints
- Service Events

---

## Container Starts Then Stops. Why?

- Application crash
- Missing configuration
- Entry point failure

---

## ALB Shows Unhealthy Targets. What Do You Check?

- Health check path
- Ports
- Application logs

---

## ECS Cannot Pull Image. What Do You Check?

- ECR permissions
- Execution role
- Network connectivity

---

## Service Not Scaling. What Do You Check?

- Policies
- Metrics
- CloudWatch alarms

---

# Senior Engineer Perspective

Most ECS incidents are caused by:

```text
Configuration
Networking
IAM
Deployments
```

not ECS itself.

The best engineers follow a systematic process.

Never:

```text
Guess
```

Always:

```text
Observe
Measure
Verify
```

Fast incident resolution comes from disciplined troubleshooting, not intuition.

---

# Key Takeaways

- Troubleshooting is a structured process.
- Start with service events, logs, and metrics.
- Most ECS failures involve networking, IAM, or deployments.
- CloudWatch is the primary debugging tool.
- Root Cause Analysis prevents repeated incidents.
- Senior engineers troubleshoot methodically rather than guessing.
