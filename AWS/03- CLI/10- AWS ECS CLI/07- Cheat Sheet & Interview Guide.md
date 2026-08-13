# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon ECS CLI commands, deployment workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used ECS CLI commands
- Manage Clusters, Services, and Tasks
- Deploy containerized applications
- Configure Auto Scaling
- Troubleshoot ECS deployments
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon ECS contains many moving parts:

- Clusters
- Task Definitions
- Services
- Tasks
- Load Balancers
- IAM
- Networking
- CloudWatch

Instead of memorizing every command, experienced engineers remember:

- Deployment workflow
- Service management
- Task lifecycle
- Monitoring
- Troubleshooting

This chapter provides a quick operational reference.

---

# CLI Namespace

General syntax:

```bash
aws ecs <operation>
```

Examples:

```bash
aws ecs list-clusters
```

```bash
aws ecs list-services
```

```bash
aws ecs list-tasks
```

---

# Cluster Commands

## List Clusters

```bash
aws ecs list-clusters
```

---

## Create Cluster

```bash
aws ecs create-cluster \
--cluster-name production-cluster
```

---

## Describe Cluster

```bash
aws ecs describe-clusters \
--clusters production-cluster
```

---

## Delete Cluster

```bash
aws ecs delete-cluster \
--cluster production-cluster
```

---

# Task Definition Commands

## Register Task Definition

```bash
aws ecs register-task-definition
```

---

## List Task Definitions

```bash
aws ecs list-task-definitions
```

---

## Describe Task Definition

```bash
aws ecs describe-task-definition
```

---

## Deregister Task Definition

```bash
aws ecs deregister-task-definition
```

---

# Task Commands

## Run Task

```bash
aws ecs run-task
```

---

## List Tasks

```bash
aws ecs list-tasks
```

---

## Describe Task

```bash
aws ecs describe-tasks
```

---

## Stop Task

```bash
aws ecs stop-task
```

---

## Execute Command

```bash
aws ecs execute-command
```

---

# Service Commands

## Create Service

```bash
aws ecs create-service
```

---

## List Services

```bash
aws ecs list-services
```

---

## Describe Service

```bash
aws ecs describe-services
```

---

## Update Service

```bash
aws ecs update-service
```

---

## Delete Service

```bash
aws ecs delete-service
```

---

# Container Instance Commands (EC2 Launch Type)

## List Container Instances

```bash
aws ecs list-container-instances
```

---

## Describe Container Instances

```bash
aws ecs describe-container-instances
```

---

# Capacity Provider Commands

## List Capacity Providers

```bash
aws ecs describe-capacity-providers
```

---

## Put Capacity Providers

```bash
aws ecs put-cluster-capacity-providers
```

---

# CloudWatch Logs Commands

## Create Log Group

```bash
aws logs create-log-group
```

---

## View Log Groups

```bash
aws logs describe-log-groups
```

---

## Tail Logs

```bash
aws logs tail /ecs/application --follow
```

---

# Service Discovery Commands

## Create Namespace

```bash
aws servicediscovery create-private-dns-namespace
```

---

## List Namespaces

```bash
aws servicediscovery list-namespaces
```

---

## Describe Namespace

```bash
aws servicediscovery get-namespace
```

---

# Application Auto Scaling Commands

## Register Scalable Target

```bash
aws application-autoscaling register-scalable-target
```

---

## Put Scaling Policy

```bash
aws application-autoscaling put-scaling-policy
```

---

## View Scaling Policies

```bash
aws application-autoscaling describe-scaling-policies
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use named AWS profile |
| `--region` | Override Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable CLI debugging |
| `--no-cli-pager` | Disable pager |

---

# ECS Components

| Component | Purpose |
|-----------|----------|
| Cluster | Logical collection of compute resources |
| Task Definition | Blueprint for containers |
| Task | Running instance of a Task Definition |
| Service | Maintains desired number of Tasks |
| Container | Running application process |
| Capacity Provider | Determines compute capacity |

---

# Launch Types

| Launch Type | Best For |
|-------------|----------|
| Fargate | Modern serverless containers |
| EC2 | Large-scale or specialized workloads |

---

# Network Modes

| Mode | Use Case |
|------|----------|
| awsvpc | Production (Recommended) |
| bridge | EC2 Docker bridge |
| host | High-performance networking |
| none | No networking |

---

# IAM Roles

| Role | Purpose |
|------|----------|
| Task Execution Role | Pull images, publish logs, access Secrets Manager |
| Task Role | Application access to AWS services |

---

# Common CloudWatch Metrics

| Metric | Description |
|---------|-------------|
| CPUUtilization | CPU usage |
| MemoryUtilization | Memory usage |
| RunningTaskCount | Running tasks |
| PendingTaskCount | Pending tasks |
| NetworkRxBytes | Incoming traffic |
| NetworkTxBytes | Outgoing traffic |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| ClusterNotFoundException | Invalid cluster | Verify cluster name |
| ServiceNotFoundException | Service missing | Verify service |
| TaskDefinitionNotFoundException | Invalid revision | Verify task definition |
| CannotPullContainerError | Image pull failed | Check ECR, IAM, networking |
| RESOURCE:CPU | CPU exhausted | Increase capacity |
| RESOURCE:MEMORY | Memory exhausted | Increase task memory |
| RESOURCE:ENI | ENI limit reached | Expand subnet or quotas |
| Essential Container Exited | Application crashed | Review CloudWatch Logs |

---

# Deployment Checklist

Before deploying:

- □ Docker image pushed to ECR
- □ Task Definition registered
- □ Task Execution Role configured
- □ Task Role configured
- □ CloudWatch Logs enabled
- □ ALB Target Group configured
- □ Health Check configured
- □ ECS Service created
- □ Desired Count verified
- □ Auto Scaling configured

---

# Production Checklist

Production ECS environments should include:

- Fargate or EC2 Capacity Provider
- Private subnets
- Application Load Balancer
- CloudWatch Logs
- Container Insights
- Auto Scaling
- IAM Task Roles
- Secrets Manager
- Route 53
- Multi-AZ deployment

---

# Troubleshooting Workflow

```text
Client

↓

Route53

↓

Application Load Balancer

↓

Target Group

↓

ECS Service

↓

Task

↓

Container

↓

CloudWatch Logs
```

---

# Production Architecture

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
Tasks
      │
      ▼
Containers
      │
      ▼
Amazon RDS
```

---

# ECS Deployment Workflow

```text
Developer

↓

Docker Build

↓

Amazon ECR

↓

Task Definition

↓

ECS Service

↓

Tasks

↓

Application Load Balancer

↓

Users
```

---

# Interview Questions

## 1. What is Amazon ECS?

**Answer**

Amazon ECS is AWS's fully managed container orchestration service used to deploy, run, and scale Docker containers using either EC2 instances or AWS Fargate.

---

## 2. What is the difference between a Task Definition and a Task?

**Answer**

A Task Definition is a versioned blueprint describing how containers should run. A Task is a running instance of that Task Definition.

---

## 3. What is an ECS Service?

**Answer**

An ECS Service maintains the desired number of running Tasks, automatically replacing failed Tasks and performing rolling deployments.

---

## 4. What is the difference between EC2 Launch Type and Fargate?

**Answer**

With EC2 Launch Type, you manage the EC2 infrastructure, operating system, and capacity. With Fargate, AWS manages the underlying infrastructure, allowing you to focus only on your containers and application configuration.

---

## 5. Why is `awsvpc` networking recommended?

**Answer**

`awsvpc` assigns each Task its own Elastic Network Interface (ENI), private IP address, and Security Group, providing VPC-native networking, stronger isolation, and compatibility with AWS Fargate.

---

## 6. What is the difference between the Task Execution Role and the Task Role?

**Answer**

The Task Execution Role is used by the ECS agent to pull container images from Amazon ECR, send logs to CloudWatch, and retrieve secrets. The Task Role is assumed by the application running inside the container and grants it permission to access AWS services such as S3, DynamoDB, or SQS.

---

## 7. How does ECS integrate with an Application Load Balancer?

**Answer**

An ECS Service registers its running Tasks with an ALB Target Group. The ALB performs health checks and routes traffic only to healthy Tasks. During deployments, new Tasks must pass health checks before receiving production traffic.

---

## 8. How does ECS Auto Scaling work?

**Answer**

Application Auto Scaling monitors CloudWatch metrics such as CPU or memory utilization and adjusts the Service's Desired Count by launching or terminating Tasks automatically.

---

## 9. How would you troubleshoot an ECS Task stuck in the PENDING state?

**Answer**

I would inspect the ECS Service events and Task details, verify available compute capacity, review subnet and ENI availability, check IAM Task Execution Role permissions, confirm the container image is accessible in Amazon ECR, and examine networking configuration such as Security Groups and NAT Gateway access.

---

## 10. What is the recommended production architecture for Amazon ECS?

**Answer**

A production ECS architecture typically consists of Route 53 directing traffic to an Application Load Balancer, which forwards requests to ECS Services running Fargate Tasks in private subnets across multiple Availability Zones. The application uses Amazon ECR for images, CloudWatch for logging and monitoring, IAM Task Roles for security, and Application Auto Scaling for elasticity.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Prefer AWS Fargate for new applications.
- Store container images in Amazon ECR.
- Keep Task Definitions immutable and version-controlled.
- Use private subnets for ECS Tasks.
- Place Application Load Balancers in public subnets.
- Use IAM Roles instead of static AWS credentials.
- Integrate ECS with CloudWatch Logs and Container Insights.
- Configure Service Auto Scaling using CloudWatch metrics.
- Use ECS Exec for production debugging instead of SSH.
- Build stateless applications that scale horizontally.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Clusters | `aws ecs list-clusters` |
| Create Cluster | `aws ecs create-cluster` |
| Register Task Definition | `aws ecs register-task-definition` |
| Run Task | `aws ecs run-task` |
| Create Service | `aws ecs create-service` |
| Update Service | `aws ecs update-service` |
| Describe Tasks | `aws ecs describe-tasks` |
| Execute Command | `aws ecs execute-command` |
| Tail Logs | `aws logs tail /ecs/app --follow` |
| Describe Services | `aws ecs describe-services` |

---

# Final Thoughts

Amazon ECS provides a fully managed platform for running containerized workloads at scale. Combined with Amazon ECR, Application Load Balancers, CloudWatch, IAM, Route 53, and AWS Fargate, ECS enables organizations to deploy secure, scalable, highly available, and production-ready applications with minimal operational overhead.

---

