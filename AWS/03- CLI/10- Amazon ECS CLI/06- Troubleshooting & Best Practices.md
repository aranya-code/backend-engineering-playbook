# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon ECS deployments and apply production-ready best practices. This chapter covers task failures, service deployment issues, networking, IAM, ECR image pulls, logging, Auto Scaling, Load Balancer integration, and operational recommendations for running highly available containerized applications.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot ECS deployments
- Debug Task failures
- Resolve Service issues
- Diagnose networking problems
- Fix image pull failures
- Troubleshoot ALB integration
- Apply production best practices

---

# ECS Troubleshooting Workflow

When an application fails:

```text
Client

↓

Route 53

↓

ALB

↓

Target Group

↓

ECS Service

↓

Task

↓

Container

↓

Application
```

Always troubleshoot from the frontend to the backend.

---

# Verify ECS Clusters

List available clusters.

```bash
aws ecs list-clusters
```

Describe a cluster.

```bash
aws ecs describe-clusters \
--clusters production-cluster
```

Verify:

- Status
- Running Tasks
- Pending Tasks
- Registered Capacity

---

# Verify ECS Services

```bash
aws ecs list-services \
--cluster production-cluster
```

Describe a Service.

```bash
aws ecs describe-services \
--cluster production-cluster \
--services web-service
```

Review:

- Desired Count
- Running Count
- Pending Count
- Deployment Status
- Events

---

# Review Service Events

Service Events often explain failures.

Example:

```text
Unable to place task

↓

Insufficient CPU
```

or

```text
Task failed ELB Health Checks
```

Always inspect events before changing configurations.

---

# Verify Running Tasks

```bash
aws ecs list-tasks \
--cluster production-cluster
```

Describe a Task.

```bash
aws ecs describe-tasks \
--cluster production-cluster \
--tasks task-id
```

Verify:

- Last Status
- Desired Status
- Launch Type
- Container Status
- Exit Code

---

# Task Stuck in PENDING

Common causes:

- No compute capacity
- Invalid subnet
- ENI limit reached
- IAM issue
- Image pull failure

Workflow:

```text
Pending

↓

Capacity

↓

Networking

↓

IAM

↓

ECR
```

---

# Task Stops Immediately

Check:

```text
Exit Code
```

Typical reasons:

- Application crash
- Invalid command
- Missing environment variables
- Port conflict

---

# View Container Logs

```bash
aws logs tail /ecs/web-app --follow
```

Always review logs before restarting tasks.

---

# Image Pull Failure

Example error:

```text
CannotPullContainerError
```

Verify:

- ECR repository
- Image tag
- Task Execution Role
- Network access

---

# ECR Authentication Issues

Verify the Task Execution Role includes:

- AmazonECSTaskExecutionRolePolicy

This allows:

- Pulling images
- Sending logs
- Accessing Secrets Manager

---

# Networking Problems

Verify:

- VPC
- Subnets
- Security Groups
- Route Tables
- NAT Gateway

Architecture:

```text
ALB

↓

Private Subnet

↓

ECS Tasks
```

---

# Security Group Issues

ALB Security Group

↓

Allows:

```text
80

443
```

Task Security Group

↓

Allows traffic only from ALB Security Group.

---

# ALB Health Check Failure

Verify:

```text
GET /health

↓

200 OK
```

Common problems:

- Wrong port
- Wrong path
- Application startup delay
- Firewall

---

# Target Never Healthy

Check:

```bash
aws elbv2 describe-target-health
```

Verify:

- Health Check Path
- Port
- Security Groups
- Application

---

# Service Cannot Reach Database

Verify:

```text
ECS Task

↓

Security Group

↓

RDS
```

Common causes:

- Incorrect Security Group
- Private subnet routing
- IAM authentication

---

# ECS Exec Not Working

Verify:

- Execute Command enabled
- Systems Manager Plugin
- IAM permissions
- Running task

---

# Environment Variables Missing

Review Task Definition.

```bash
aws ecs describe-task-definition \
--task-definition web-app
```

Verify:

- Environment variables
- Secrets
- Parameters

---

# Secrets Manager Issues

Verify:

- Secret ARN
- Task Role permissions
- Secret exists

---

# CloudWatch Logs Missing

Check:

- awslogs driver
- Log Group
- IAM permissions
- Region

---

# Deployment Never Completes

Review:

```text
Deployment

↓

Health Checks

↓

Task Startup

↓

ALB Registration
```

---

# Auto Scaling Not Working

Verify:

```text
CloudWatch Alarm

↓

Scaling Policy

↓

Desired Count
```

---

# Service Discovery Problems

Verify:

- Cloud Map Namespace
- DNS
- Registration
- VPC DNS settings

---

# Fargate Task Doesn't Start

Common causes:

- Invalid CPU/Memory combination
- ENI unavailable
- IAM Role
- Unsupported Region

---

# Common Errors

## ClusterNotFoundException

Verify:

- Cluster name
- Region
- AWS Account

---

## ServiceNotFoundException

Verify:

- Service exists
- Cluster name

---

## TaskDefinitionNotFoundException

Verify:

- Family
- Revision

---

## CannotPullContainerError

Verify:

- Image exists
- Repository permissions
- Task Execution Role
- Network connectivity

---

## RESOURCE:CPU

Insufficient CPU available.

Increase:

- Cluster capacity
- Fargate limits

---

## RESOURCE:MEMORY

Insufficient memory available.

Review Task Definition.

---

## RESOURCE:ENI

No available Elastic Network Interfaces.

Solutions:

- Larger subnet
- Fewer running Tasks
- Service quotas

---

## Essential Container Exited

Review:

```text
CloudWatch Logs

↓

Application Error
```

The Service will automatically replace the Task.

---

# CloudWatch Monitoring

Monitor:

- CPUUtilization
- MemoryUtilization
- RunningTaskCount
- PendingTaskCount
- TaskRestarts
- NetworkRxBytes
- NetworkTxBytes

---

# CloudWatch Alarms

Recommended alarms:

```text
CPU > 80%
```

```text
Memory > 85%
```

```text
Running Tasks < Desired Count
```

```text
Task Failures > 0
```

---

# Production Best Practices

## Use Fargate

Prefer Fargate unless EC2-specific features are required.

---

## Deploy in Private Subnets

Recommended architecture:

```text
Internet

↓

ALB

↓

Private ECS Tasks
```

---

## Always Use Load Balancers

Avoid exposing Tasks directly.

Prefer:

```text
Route53

↓

ALB

↓

ECS
```

---

## Store Images in Amazon ECR

Avoid third-party registries for production workloads.

---

## Version Task Definitions

Never overwrite production revisions.

Example:

```text
api:12

↓

api:13
```

---

## Use IAM Roles

Never store AWS credentials inside containers.

Use:

```text
Task Role
```

---

## Configure Health Checks

Every Service should expose:

```text
/health
```

---

## Enable Logging

Send logs to:

```text
CloudWatch Logs
```

---

## Monitor Continuously

Use:

- CloudWatch
- Container Insights
- X-Ray
- CloudWatch Alarms

---

## Keep Applications Stateless

Avoid storing session data inside containers.

Instead use:

- Redis
- DynamoDB
- ElastiCache

---

# Real-World Workflow

```text
Build Docker Image

↓

Push to ECR

↓

Register Task Definition

↓

Deploy ECS Service

↓

Health Checks

↓

CloudWatch

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
Amazon ECS Service
      │
      ▼
Running Tasks
      │
      ▼
Containers
      │
      ▼
CloudWatch Logs
```

A production ECS environment relies on continuous monitoring, health checks, logging, IAM roles, and Load Balancer integration to maintain application availability and quickly recover from failures.

---

# Interview Note

### Question

**How would you troubleshoot an ECS Service where tasks keep restarting?**

### Answer

I would first inspect the ECS Service events and task status using `describe-services` and `describe-tasks`. Next, I would review CloudWatch Logs to identify application errors or container crashes. I would verify the Task Definition, including the container image, environment variables, CPU and memory settings, IAM roles, and Secrets Manager configuration. If the service is behind an Application Load Balancer, I would check the target group's health checks, security groups, and networking configuration. Finally, I would review CloudWatch metrics and ECS deployment events to determine whether the issue is related to application failures, infrastructure limits, or deployment configuration.

---

# Key Takeaways

- Troubleshoot ECS from the client to the container.
- ECS Service events often identify deployment failures.
- CloudWatch Logs are the primary source for application debugging.
- IAM Task Execution Roles are required for pulling images and publishing logs.
- ALB Health Checks determine whether tasks receive production traffic.
- Private subnet networking and Security Groups are common sources of connectivity issues.
- Combining CloudWatch, Container Insights, ECS Exec, and proper deployment practices results in reliable, production-grade ECS environments.