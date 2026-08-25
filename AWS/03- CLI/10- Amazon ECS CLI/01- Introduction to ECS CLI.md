# Introduction to ECS CLI

> Learn how to deploy, manage, and scale containerized applications using Amazon Elastic Container Service (Amazon ECS) and the AWS Command Line Interface (AWS CLI). This chapter introduces ECS architecture, clusters, tasks, services, launch types, and the core CLI commands used to manage container workloads.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon ECS
- Understand containers and orchestration
- Understand ECS architecture
- Understand ECS components
- Learn ECS launch types
- Navigate ECS CLI commands
- Build a strong foundation for containerized applications

---

# Why Learn Amazon ECS?

Modern applications are increasingly packaged as containers.

Instead of deploying directly onto EC2:

```text
Application

↓

EC2
```

Applications are packaged as:

```text
Docker Image

↓

Container

↓

ECS
```

Benefits include:

- Portability
- Scalability
- Faster deployments
- Consistent environments
- Easier CI/CD
- Microservices architecture

Amazon ECS is AWS's fully managed container orchestration service.

---

# What is Amazon ECS?

Amazon Elastic Container Service (Amazon ECS) is a fully managed container orchestration platform.

It helps you:

- Run containers
- Scale containers
- Monitor containers
- Deploy containers
- Recover failed containers

without managing complex orchestration software.

---

# What is a Container?

A container packages:

- Application
- Runtime
- Dependencies
- Libraries
- Configuration

into one deployable unit.

```text
Container

│

├── Application

├── Runtime

├── Libraries

└── Dependencies
```

---

# Why Containers?

Traditional deployment:

```text
Application

↓

Operating System

↓

Server
```

Different servers may behave differently.

Container deployment:

```text
Docker Image

↓

Container

↓

Runs Anywhere
```

Containers provide consistency.

---

# ECS Architecture

```text
Cluster

↓

Service

↓

Tasks

↓

Containers
```

---

# ECS Components

Amazon ECS consists of:

```text
Amazon ECS

│

├── Cluster

├── Task Definition

├── Task

├── Service

├── Container

└── Capacity
```

---

# What is a Cluster?

A Cluster is a logical grouping of compute resources.

```text
Cluster

↓

EC2

↓

Fargate
```

Applications run inside clusters.

---

# What is a Task Definition?

A Task Definition is a blueprint.

It defines:

- Docker image
- CPU
- Memory
- Environment variables
- Ports
- Volumes
- IAM role

---

# What is a Task?

A Task is a running instance of a Task Definition.

```text
Task Definition

↓

Run

↓

Task
```

---

# What is a Service?

A Service keeps Tasks running.

Example:

```text
Desired Tasks

↓

3

↓

Running Tasks

↓

3
```

If one task crashes:

```text
Task Failed

↓

Service

↓

Launch Replacement
```

---

# Launch Types

Amazon ECS supports two launch types.

```text
ECS

│

├── EC2

└── Fargate
```

---

# EC2 Launch Type

You manage:

- EC2
- Scaling
- AMIs
- Capacity

AWS manages:

- ECS Scheduler

---

# Fargate Launch Type

AWS manages:

- Servers
- Scaling infrastructure
- Operating System

You manage only:

- Containers

This is the recommended option for most new applications.

---

# ECS Deployment Workflow

```text
Docker Image

↓

Amazon ECR

↓

Task Definition

↓

Service

↓

Running Tasks
```

---

# ECS CLI Namespace

Amazon ECS uses:

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

# List ECS Clusters

```bash
aws ecs list-clusters
```

---

# Describe a Cluster

```bash
aws ecs describe-clusters \
--clusters production-cluster
```

---

# List Services

```bash
aws ecs list-services \
--cluster production-cluster
```

---

# List Running Tasks

```bash
aws ecs list-tasks \
--cluster production-cluster
```

---

# Verify AWS Identity

Before deploying containers:

```bash
aws sts get-caller-identity
```

---

# Global CLI Options

Examples:

```bash
aws ecs list-clusters \
--profile production
```

```bash
aws ecs list-clusters \
--region ap-south-1
```

---

# Production Tip

Never deploy containers directly.

Recommended architecture:

```text
Route53

↓

ALB

↓

ECS Service

↓

Tasks

↓

Containers
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
Amazon ECS Service
      │
      ▼
Tasks
      │
      ▼
Containers
```

Amazon ECS provides a fully managed platform for running and scaling containerized applications while integrating seamlessly with VPC, IAM, CloudWatch, Auto Scaling, and Elastic Load Balancing.

---

# Interview Note

### Question

**What is Amazon ECS?**

### Answer

Amazon Elastic Container Service (Amazon ECS) is AWS's fully managed container orchestration service that deploys, manages, and scales Docker containers. It supports both EC2 and AWS Fargate launch types and integrates with services such as Amazon ECR, Application Load Balancers, CloudWatch, IAM, and Auto Scaling to simplify containerized application deployments.

---

# Key Takeaways

- Amazon ECS is AWS's managed container orchestration platform.
- Containers package applications with all dependencies.
- Clusters organize compute resources.
- Task Definitions define how containers run.
- Tasks are running instances of Task Definitions.
- Services maintain the desired number of running Tasks.
- ECS supports both EC2 and Fargate launch types.
- The AWS CLI uses the `aws ecs` namespace for ECS operations.