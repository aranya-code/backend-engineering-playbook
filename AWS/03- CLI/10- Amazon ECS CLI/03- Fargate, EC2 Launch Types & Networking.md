# Fargate, EC2 Launch Types & Networking

> Learn how Amazon ECS runs containers using AWS Fargate and EC2 launch types, understand ECS networking modes, awsvpc networking, security groups, ENIs, IAM roles, capacity providers, and production networking best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand ECS Launch Types
- Compare Fargate and EC2
- Configure ECS Networking
- Understand ENIs
- Configure Security Groups
- Understand Capacity Providers
- Design production networking architectures

---

# ECS Launch Types

Amazon ECS supports two primary launch types.

```text
Amazon ECS

│

├── EC2 Launch Type

└── AWS Fargate
```

Each determines where your containers run.

---

# EC2 Launch Type

With EC2 Launch Type:

You manage:

- EC2 Instances
- Scaling
- Operating System
- AMIs
- Capacity

AWS manages:

- ECS Scheduler
- Container placement

---

# EC2 Architecture

```text
Amazon ECS

↓

Cluster

↓

EC2 Instance

↓

Docker

↓

Containers
```

---

# Advantages of EC2

- Lower cost at scale
- Full OS access
- GPU support
- Custom AMIs
- Specialized hardware
- Greater flexibility

---

# Disadvantages of EC2

You are responsible for:

- Instance patching
- Capacity planning
- Scaling infrastructure
- AMI updates
- Operating system maintenance

---

# AWS Fargate

AWS Fargate is serverless compute for containers.

AWS manages:

- EC2
- Scaling infrastructure
- Operating System
- Capacity
- Patching

You manage only:

- Containers

---

# Fargate Architecture

```text
Amazon ECS

↓

Fargate

↓

Container

↓

Application
```

No EC2 instances are visible.

---

# Advantages of Fargate

- No server management
- Automatic infrastructure
- Better isolation
- Simpler deployments
- Pay per task
- Fast scaling

---

# Disadvantages of Fargate

- Higher cost for large workloads
- Less infrastructure control
- Limited host customization

---

# EC2 vs Fargate

| Feature | EC2 | Fargate |
|----------|-----|----------|
| Manage Servers | Yes | No |
| OS Access | Yes | No |
| Scaling Infrastructure | Manual | AWS |
| Pay For | EC2 Instances | Running Tasks |
| Best For | Large clusters | Modern applications |
| Startup Time | Moderate | Fast |

---

# When to Choose EC2

Use EC2 when:

- Running GPU workloads
- Large-scale clusters
- Long-running services
- Specialized hardware
- Cost optimization

---

# When to Choose Fargate

Use Fargate when:

- Building microservices
- Running APIs
- Event-driven workloads
- Small-to-medium applications
- Minimal operational overhead

---

# Launch a Fargate Task

```bash
aws ecs run-task \
--cluster production-cluster \
--launch-type FARGATE \
--task-definition web-app
```

---

# Launch an EC2 Task

```bash
aws ecs run-task \
--cluster production-cluster \
--launch-type EC2 \
--task-definition web-app
```

---

# Networking in ECS

Each Task must communicate with:

- Clients
- Load Balancers
- Databases
- Other services
- AWS APIs

Networking is therefore a critical part of ECS.

---

# Network Modes

Amazon ECS supports:

```text
Network Modes

│

├── awsvpc

├── bridge

├── host

└── none
```

---

# awsvpc Mode

Recommended for production.

Each Task receives:

- Dedicated ENI
- Private IP
- Security Group

Architecture:

```text
Task

↓

Elastic Network Interface (ENI)

↓

Private IP
```

---

# Why awsvpc?

Benefits:

- Strong isolation
- Independent Security Groups
- VPC-native networking
- Required for Fargate

---

# Bridge Mode

Containers share the EC2 network stack using Docker bridge networking.

```text
EC2

↓

Docker Bridge

↓

Containers
```

Mostly used with EC2 launch type.

---

# Host Mode

Container shares the EC2 host network.

```text
Container

↓

EC2 Network
```

Advantages:

- Lower latency
- No NAT

Disadvantages:

- Port conflicts
- Less isolation

---

# None Mode

No networking.

```text
Container

↓

No Network
```

Rarely used.

---

# Elastic Network Interface (ENI)

Each Fargate Task receives its own ENI.

```text
Task

↓

ENI

↓

Private IP

↓

Security Group
```

This allows Tasks to behave like individual EC2 instances on the network.

---

# Configure awsvpc

Example:

```json
"networkMode": "awsvpc"
```

---

# Run Task with Networking

```bash
aws ecs run-task \
--cluster production-cluster \
--launch-type FARGATE \
--network-configuration \
"awsvpcConfiguration={
subnets=[subnet-123],
securityGroups=[sg-123],
assignPublicIp=ENABLED}"
```

---

# Public vs Private Subnets

Internet-facing services:

```text
Internet

↓

Public Subnet

↓

ALB

↓

Private Subnet

↓

ECS Tasks
```

Recommended production design.

---

# Security Groups

Each Task can have its own Security Group.

Example:

```text
ALB

↓

Security Group

↓

ECS Task

↓

Security Group
```

Restrict inbound access to only trusted sources.

---

# IAM Roles

Amazon ECS uses two important IAM roles.

```text
IAM

│

├── Task Execution Role

└── Task Role
```

---

# Task Execution Role

Used by ECS Agent to:

- Pull images from ECR
- Send logs to CloudWatch
- Retrieve Secrets Manager values

---

# Task Role

Used by the application itself.

Example:

```text
Application

↓

IAM Task Role

↓

S3
```

This avoids storing AWS credentials inside containers.

---

# Capacity Providers

Capacity Providers manage how Tasks obtain compute resources.

```text
Capacity Provider

│

├── EC2

├── Fargate

└── Fargate Spot
```

---

# Fargate Spot

Lower-cost Fargate capacity.

Benefits:

- Significant cost savings

Trade-off:

- Tasks may be interrupted by AWS with short notice.

Suitable for:

- Batch jobs
- Background workers
- CI/CD pipelines

---

# Multi-AZ Networking

Deploy Tasks across multiple Availability Zones.

```text
ALB

↓

AZ-A

↓

Task

────────────

AZ-B

↓

Task
```

Improves availability.

---

# Common Errors

## RESOURCE:ENI

No available ENIs.

Solutions:

- Increase subnet capacity
- Review ENI limits
- Use larger subnets

---

## InvalidSubnet

Verify:

- Subnet exists
- Correct VPC
- Region

---

## Security Group Blocks Traffic

Verify:

- Inbound rules
- Outbound rules
- ALB Security Group
- Task Security Group

---

## Cannot Pull Image

Verify:

- Task Execution Role
- ECR permissions
- Network connectivity
- NAT Gateway (for private subnets)

---

# Production Best Practices

- Prefer Fargate for new applications.
- Use `awsvpc` networking.
- Place ECS Tasks in private subnets.
- Place ALBs in public subnets.
- Assign dedicated Security Groups to Tasks.
- Use IAM Task Roles instead of static credentials.
- Spread Tasks across multiple Availability Zones.
- Use Capacity Providers for flexible scaling.
- Use Fargate Spot for fault-tolerant background workloads.

---

# Real-World Workflow

```text
Create Cluster

↓

Register Task Definition

↓

Choose Launch Type

↓

Configure Networking

↓

Deploy Service

↓

Production
```

---

# Architecture Note

```text
Internet
      │
      ▼
Application Load Balancer
      │
      ▼
Private Subnets
      │
      ▼
Amazon ECS Service
      │
      ▼
Fargate Tasks
      │
      ▼
Amazon RDS
```

In modern AWS architectures, ECS Fargate tasks are typically deployed in private subnets behind an Application Load Balancer, with networking managed using `awsvpc` mode and secured through Security Groups and IAM Roles.

---

# Interview Note

### Question

**What is the difference between ECS EC2 Launch Type and AWS Fargate?**

### Answer

With the **EC2 Launch Type**, you manage the underlying EC2 instances, including operating system updates, scaling, and capacity planning, while ECS manages task scheduling. With **AWS Fargate**, AWS manages the underlying infrastructure, allowing you to focus only on your containers and application configuration. Fargate is generally preferred for modern cloud-native applications because it reduces operational overhead, whereas EC2 provides greater flexibility and can be more cost-effective for large, long-running workloads.

---

# Key Takeaways

- ECS supports both EC2 and AWS Fargate launch types.
- Fargate eliminates server management and is recommended for most new applications.
- `awsvpc` is the preferred network mode and is required for Fargate.
- Each Fargate Task receives its own ENI, private IP, and Security Group.
- Separate Task Execution Roles from Task Roles for security.
- Capacity Providers simplify compute management and support Fargate Spot for cost optimization.
- Deploy ECS tasks in private subnets behind an Application Load Balancer for production environments.