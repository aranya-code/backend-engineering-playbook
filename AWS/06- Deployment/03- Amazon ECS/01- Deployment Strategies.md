# ECS Deployment Strategies

# Why Deployments Matter

Deployments are one of the highest-risk operations in production.

Every deployment introduces the possibility of:

- Downtime
- Bugs
- Performance Issues
- Service Outages

A good deployment strategy minimizes risk.

---

# What is a Deployment?

A deployment is the process of replacing an existing application version with a new version.

Example:

```text
Version 1
    ↓
Version 2
```

The challenge:

```text
How do we upgrade without downtime?
```

---

# ECS Deployment Workflow

```text
New Task Definition
        ↓
Service Update
        ↓
New Tasks Created
        ↓
Old Tasks Removed
```

---

# ECS Deployment Types

Common deployment strategies:

```text
Rolling Deployment
Blue/Green Deployment
Canary Deployment
```

---

# Rolling Deployment

Default ECS deployment strategy.

Old tasks are gradually replaced.

---

# Example

Current:

```text
Task A v1
Task B v1
Task C v1
```

Deploy:

```text
Version 2
```

---

ECS gradually replaces:

```text
Task A v2
Task B v2
Task C v2
```

---

# Benefits

- Simple
- Automated
- No additional infrastructure
- Low operational complexity

---

# Drawbacks

Rollback can take time.

Bad deployments may affect users before detection.

---

# Deployment Configuration

Two critical settings:

```text
Minimum Healthy Percent
Maximum Percent
```

---

# Minimum Healthy Percent

Controls minimum healthy tasks during deployment.

Example:

```text
100%
```

All tasks remain available.

---

Desired Tasks:

```text
4
```

Healthy Tasks Required:

```text
4
```

---

# Maximum Percent

Controls temporary capacity during deployment.

Example:

```text
200%
```

Desired Tasks:

```text
4
```

Maximum Running:

```text
8
```

during deployment.

---

# Example Deployment

Current:

```text
4 Tasks
```

Maximum Percent:

```text
200%
```

ECS can temporarily run:

```text
8 Tasks
```

to ensure zero downtime.

---

# Rolling Deployment Workflow

```text
Create New Task
      ↓
Health Check Passes
      ↓
Remove Old Task
      ↓
Repeat
```

---

# Blue/Green Deployment

Two environments exist simultaneously.

```text
Blue
Green
```

---

# Blue Environment

Current production.

```text
Users
 ↓
Blue
```

---

# Green Environment

New version.

```text
Green
```

Receives no traffic initially.

---

# Deployment Flow

```text
Blue
 ↓
Green Deployed
 ↓
Testing
 ↓
Traffic Shift
```

---

# Advantages

- Safer releases
- Fast rollback
- Better testing

---

# Disadvantages

- Higher cost
- Additional infrastructure

---

# Blue/Green Rollback

If problems occur:

```text
Traffic
 ↓
Back To Blue
```

Rollback is nearly instant.

---

# Canary Deployment

Deploy to a small percentage of users first.

Example:

```text
5% Traffic
 ↓
Version 2
```

---

Remaining:

```text
95% Traffic
 ↓
Version 1
```

---

# Benefits

- Reduced risk
- Real-world validation
- Faster issue detection

---

# Canary Workflow

```text
5%
 ↓
25%
 ↓
50%
 ↓
100%
```

Gradual rollout.

---

# ECS Deployment Circuit Breaker

Protects against bad deployments.

---

# Example

New deployment:

```text
Version 2
```

---

Health checks fail.

ECS detects:

```text
Deployment Failure
```

---

Action:

```text
Rollback
```

Automatically.

---

# Why Circuit Breakers Matter

Without:

```text
Broken Deployment
 ↓
Production Outage
```

---

With Circuit Breaker:

```text
Broken Deployment
 ↓
Automatic Rollback
```

---

# Health Checks and Deployments

Deployments rely heavily on:

```text
Container Health Checks
ALB Health Checks
```

---

Deployment Success:

```text
Health Checks Pass
```

---

Deployment Failure:

```text
Health Checks Fail
```

---

# ECS + ALB Deployment Flow

```text
New Task
 ↓
Target Group Registration
 ↓
Health Check
 ↓
Traffic Allowed
```

---

If unhealthy:

```text
Traffic Blocked
```

---

# Zero-Downtime Deployments

Goal:

```text
Users Never Notice Deployment
```

Requirements:

- Health Checks
- Proper Deployment Settings
- Load Balancer Integration

---

# ECS and CodeDeploy

AWS CodeDeploy supports:

```text
Blue/Green Deployments
```

with ECS.

---

Benefits

- Automated traffic shifting
- Rollback support
- Advanced release strategies

---

# Deployment Failure Scenarios

## Application Crash

Symptoms:

```text
Task Stops
```

---

## Failed Health Checks

Symptoms:

```text
No Healthy Targets
```

---

## Wrong Environment Variables

Symptoms:

```text
Application Startup Failure
```

---

## Database Connectivity Issues

Symptoms:

```text
Health Check Failure
```

---

# Production Deployment Example

FastAPI Service

Current:

```text
v1
```

Deploy:

```text
v2
```

---

Process:

```text
Create New Tasks
 ↓
Health Checks Pass
 ↓
Shift Traffic
 ↓
Remove Old Tasks
```

---

No downtime.

---

# Release Strategies

## Conservative

Deploy slowly.

Benefits:

- Lower risk

---

## Aggressive

Deploy quickly.

Benefits:

- Faster releases

Risk:

- Larger blast radius

---

# Production Best Practices

## Use Health Checks

Always validate deployments.

---

## Enable Circuit Breakers

Automatic rollback protection.

---

## Prefer Blue/Green For Critical Systems

Safer releases.

---

## Avoid Large Deployments

Smaller changes reduce risk.

---

## Monitor Deployments

Track:

- Errors
- Latency
- CPU
- Memory

---

# Common Mistakes

## No Rollback Plan

Risk:

Extended outages.

---

## Ignoring Health Checks

Broken tasks receive traffic.

---

## Deploying Large Changes

Increases deployment risk.

---

## Disabling Monitoring

Problems go unnoticed.

---

# Troubleshooting

## Deployment Stuck

Check:

```text
Task Status
Health Checks
Service Events
```

---

## Continuous Rollbacks

Check:

```text
Application Logs
Environment Variables
Database Connectivity
```

---

## No Healthy Targets

Check:

```text
Target Groups
Ports
Health Check Paths
```

---

# Common Interview Questions

## What is a Rolling Deployment?

Gradually replaces old tasks.

---

## What is Blue/Green Deployment?

Two environments with controlled traffic switching.

---

## What is a Canary Deployment?

Release to a small percentage of users first.

---

## What is a Deployment Circuit Breaker?

Automatically rolls back failed deployments.

---

## Why Use Minimum Healthy Percent?

Maintain availability during deployments.

---

## Why Use Maximum Percent?

Allow temporary extra capacity.

---

# Senior Engineer Perspective

Deployments are not merely technical operations.

They are risk-management activities.

Senior engineers optimize for:

- Reliability
- Recoverability
- Observability
- Business Continuity

The best deployment strategy is not always the fastest.

It is the one that minimizes user impact while maintaining delivery velocity.

---

# Key Takeaways

- Rolling Deployments are the ECS default.
- Blue/Green Deployments provide safer releases.
- Canary Deployments reduce rollout risk.
- Circuit Breakers enable automatic rollback.
- Health Checks determine deployment success.
- Proper deployment settings enable zero downtime.
- Deployment strategies directly impact system reliability.
