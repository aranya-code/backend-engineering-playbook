# Deployments, Auto Scaling & Load Balancing

> Learn how Amazon ECS performs application deployments, integrates with Application Load Balancers (ALB), automatically scales services, and enables zero-downtime deployments using the AWS CLI. This chapter covers rolling deployments, blue/green deployments, deployment strategies, Service Auto Scaling, and production deployment best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Deploy ECS Services
- Perform rolling deployments
- Understand Blue/Green deployments
- Integrate ECS with ALB
- Configure Service Auto Scaling
- Monitor deployments
- Build production deployment pipelines

---

# Deployment Workflow

A typical ECS deployment looks like:

```text
Docker Image

↓

Amazon ECR

↓

Task Definition

↓

ECS Service

↓

Application Load Balancer

↓

Users
```

---

# ECS Deployment Types

Amazon ECS supports multiple deployment strategies.

```text
Deployments

│

├── Rolling Update

├── Blue/Green

└── External
```

---

# Rolling Deployment

The default ECS deployment strategy.

```text
Version 1

↓

Launch Version 2

↓

Health Check

↓

Stop Version 1
```

There is no downtime if enough healthy tasks are available.

---

# Rolling Deployment Workflow

```text
Old Task

↓

New Task

↓

Healthy?

↓

Remove Old Task
```

The service gradually replaces old tasks.

---

# Deployment Configuration

Two important settings control rolling deployments.

```text
Deployment Configuration

│

├── Minimum Healthy Percent

└── Maximum Percent
```

---

# Minimum Healthy Percent

Specifies the minimum percentage of healthy tasks during deployment.

Example:

```text
Desired Tasks

↓

4

Minimum Healthy

↓

50%
```

At least two tasks remain available during deployment.

---

# Maximum Percent

Defines the maximum number of tasks allowed during deployment.

Example:

```text
Desired

↓

4

Maximum

↓

200%
```

ECS may temporarily run up to eight tasks.

---

# Update a Service

Deploy a new application version.

```bash
aws ecs update-service \
--cluster production-cluster \
--service web-service \
--task-definition web-app:5
```

A rolling deployment begins automatically.

---

# Force a New Deployment

Redeploy without changing the Task Definition.

```bash
aws ecs update-service \
--cluster production-cluster \
--service web-service \
--force-new-deployment
```

Useful when:

- Pulling a newer image with the same tag
- Restarting containers
- Refreshing tasks

---

# View Deployments

```bash
aws ecs describe-services \
--cluster production-cluster \
--services web-service
```

Displays:

- Active deployment
- Running count
- Pending count
- Deployment status

---

# Deployment Lifecycle

```text
Primary

↓

Active

↓

Completed
```

Failed deployments trigger rollback if configured.

---

# Blue/Green Deployment

Blue/Green deployments use two separate environments.

```text
Blue

↓

Current Production

────────────

Green

↓

New Version
```

After validation:

```text
Traffic

↓

Green
```

---

# Blue/Green Architecture

```text
Users

↓

Application Load Balancer

↓

Blue Target Group

────────────

Green Target Group
```

Traffic switches between Target Groups.

---

# ECS Blue/Green

Blue/Green deployments are commonly managed using:

```text
Amazon ECS

↓

AWS CodeDeploy
```

Benefits:

- Near-zero downtime
- Fast rollback
- Safer production deployments

---

# Canary Deployment

Traffic is gradually shifted.

```text
Version 1

↓

95%

────────────

Version 2

↓

5%
```

Traffic gradually increases.

---

# Deployment Controller

Supported deployment controllers:

```text
Deployment Controller

│

├── ECS

├── CODE_DEPLOY

└── EXTERNAL
```

---

# ECS with Application Load Balancer

Typical production architecture:

```text
Users

↓

Route 53

↓

Application Load Balancer

↓

Target Group

↓

ECS Service

↓

Tasks
```

---

# Register ECS with ALB

When creating the Service:

```text
Service

↓

Target Group

↓

Application Load Balancer
```

Tasks automatically register with the Target Group.

---

# Target Registration

```text
New Task

↓

Register

↓

Health Check

↓

Healthy

↓

Receive Traffic
```

---

# Deregistration

During deployments:

```text
Task

↓

Draining

↓

Finish Requests

↓

Stop
```

No active client requests are interrupted.

---

# Service Auto Scaling

Amazon ECS supports automatic scaling.

```text
CloudWatch

↓

Scaling Policy

↓

ECS Service

↓

More Tasks
```

---

# Scaling Policies

Supported policies:

```text
Scaling Policies

│

├── Target Tracking

├── Step Scaling

└── Scheduled Scaling
```

---

# Target Tracking

Example:

```text
CPU > 70%

↓

Add Tasks
```

Later:

```text
CPU < 30%

↓

Remove Tasks
```

---

# Step Scaling

Example:

```text
CPU > 80%

↓

+2 Tasks
```

```text
CPU > 90%

↓

+5 Tasks
```

---

# Scheduled Scaling

Useful for predictable traffic.

```text
Morning

↓

Scale Out

────────────

Night

↓

Scale In
```

---

# Register a Scalable Target

```bash
aws application-autoscaling register-scalable-target \
--service-namespace ecs \
--resource-id service/production-cluster/web-service \
--scalable-dimension ecs:service:DesiredCount \
--min-capacity 2 \
--max-capacity 10
```

---

# Create a Scaling Policy

```bash
aws application-autoscaling put-scaling-policy \
--service-namespace ecs \
--policy-name cpu-scaling
```

---

# View Scaling Policies

```bash
aws application-autoscaling describe-scaling-policies \
--service-namespace ecs
```

---

# Deployment Monitoring

Useful metrics:

- CPUUtilization
- MemoryUtilization
- RunningTaskCount
- PendingTaskCount
- TargetResponseTime
- HealthyHostCount

---

# CloudWatch Integration

```text
CloudWatch

↓

Alarm

↓

Application Auto Scaling

↓

ECS Service
```

Scaling decisions are driven by CloudWatch metrics.

---

# Deployment States

Typical deployment states:

```text
In Progress

↓

Completed

↓

Failed
```

---

# Common Errors

## Deployment Stuck

Verify:

- Task health
- Container startup
- Target Group health
- Application logs

---

## Tasks Never Become Healthy

Check:

- Health Check endpoint
- Security Groups
- Container port
- ALB Target Group

---

## Scaling Not Triggered

Verify:

- CloudWatch metrics
- Scaling policy
- Min/Max capacity
- Desired count

---

## Deployment Rollback

Possible causes:

- Application crash
- Failed Health Checks
- Invalid image
- Incorrect Task Definition

---

# Production Best Practices

- Use immutable Task Definition revisions.
- Prefer rolling deployments for routine releases.
- Use Blue/Green deployments for critical production systems.
- Never deploy directly to production without Health Checks.
- Integrate ECS Services with Application Load Balancers.
- Enable automatic Service Auto Scaling.
- Configure deployment alarms.
- Monitor deployment progress using CloudWatch.

---

# Real-World Workflow

```text
Build Docker Image

↓

Push to Amazon ECR

↓

Register Task Definition

↓

Update ECS Service

↓

Rolling Deployment

↓

Health Checks

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
Amazon Route 53
      │
      ▼
Application Load Balancer
      │
      ▼
Target Group
      │
      ▼
Amazon ECS Service
      │
      ▼
Tasks
      │
      ▼
Containers
```

Amazon ECS integrates seamlessly with Application Load Balancers and Application Auto Scaling to provide highly available, self-healing, and automatically scalable container deployments.

---

# Interview Note

### Question

**How does ECS perform zero-downtime deployments?**

### Answer

By default, Amazon ECS performs rolling deployments. When a new Task Definition revision is deployed, ECS launches new tasks before terminating old ones. The new tasks must successfully pass the configured Application Load Balancer health checks before they begin receiving production traffic. ECS respects the configured **Minimum Healthy Percent** and **Maximum Percent** settings to ensure that a sufficient number of healthy tasks remain available throughout the deployment. For more advanced deployment strategies, ECS also supports Blue/Green deployments through AWS CodeDeploy.

---

# Key Takeaways

- ECS supports Rolling, Blue/Green, and External deployment strategies.
- Rolling deployments are the default and provide near zero-downtime updates.
- ECS automatically registers and deregisters tasks with Application Load Balancers.
- Service Auto Scaling adjusts the number of running tasks based on CloudWatch metrics.
- Deployment configuration is controlled using Minimum Healthy Percent and Maximum Percent.
- Blue/Green deployments offer safer releases and rapid rollback capabilities.
- Combining ECS, ALB, CloudWatch, and Application Auto Scaling enables resilient, production-grade container platforms.