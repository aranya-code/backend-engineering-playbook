# Clusters, Task Definitions & Services

> Learn how to create and manage Amazon ECS Clusters, Task Definitions, Services, and Tasks using the AWS CLI. This chapter covers the core building blocks of ECS, task lifecycle, service management, revisions, deployments, and production best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create ECS Clusters
- Understand Task Definitions
- Register Task Definitions
- Run Tasks
- Create Services
- Understand Task Lifecycle
- Build production-ready ECS deployments

---

# ECS Architecture

The basic ECS architecture looks like this:

```text
Cluster

↓

Service

↓

Task

↓

Container
```

Everything in ECS begins with a Cluster.

---

# What is an ECS Cluster?

A Cluster is a logical collection of compute resources where containers run.

A Cluster can contain:

- EC2 Instances
- Fargate Tasks
- ECS Services
- Standalone Tasks

```text
Cluster

│

├── Service A

├── Service B

└── Tasks
```

---

# Create a Cluster

```bash
aws ecs create-cluster \
--cluster-name production-cluster
```

Returns:

- Cluster ARN
- Cluster Name
- Status
- Registered Capacity

---

# List Clusters

```bash
aws ecs list-clusters
```

---

# Describe Cluster

```bash
aws ecs describe-clusters \
--clusters production-cluster
```

Displays:

- Status
- Active Services
- Running Tasks
- Pending Tasks
- Registered Container Instances

---

# Delete Cluster

```bash
aws ecs delete-cluster \
--cluster production-cluster
```

The cluster must not contain running services or tasks.

---

# What is a Task Definition?

A Task Definition is the blueprint for running containers.

It specifies:

- Docker image
- CPU
- Memory
- Network Mode
- Environment Variables
- IAM Role
- Logging
- Port Mapping

---

# Task Definition Architecture

```text
Task Definition

│

├── Docker Image

├── CPU

├── Memory

├── Ports

├── Environment Variables

└── IAM Role
```

---

# Task Definition Revisions

Task Definitions are immutable.

Example:

```text
web-app:1

↓

web-app:2

↓

web-app:3
```

Each update creates a new revision.

---

# Register a Task Definition

```bash
aws ecs register-task-definition \
--cli-input-json file://task-definition.json
```

This creates a new revision.

---

# List Task Definitions

```bash
aws ecs list-task-definitions
```

---

# Describe Task Definition

```bash
aws ecs describe-task-definition \
--task-definition web-app
```

---

# Deregister Task Definition

```bash
aws ecs deregister-task-definition \
--task-definition web-app:5
```

Old revisions remain available until deregistered.

---

# Example Task Definition

```json
{
  "family": "web-app",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "123456789012.dkr.ecr.ap-south-1.amazonaws.com/web:v1",
      "cpu": 256,
      "memory": 512,
      "essential": true
    }
  ]
}
```

---

# What is a Task?

A Task is a running copy of a Task Definition.

```text
Task Definition

↓

Run

↓

Task
```

---

# Run a Standalone Task

```bash
aws ecs run-task \
--cluster production-cluster \
--task-definition web-app
```

Standalone Tasks are useful for:

- Batch jobs
- Data processing
- Scheduled jobs
- Database migrations

---

# List Running Tasks

```bash
aws ecs list-tasks \
--cluster production-cluster
```

---

# Describe Tasks

```bash
aws ecs describe-tasks \
--cluster production-cluster \
--tasks task-id
```

Displays:

- Task ARN
- Status
- Launch Type
- Container Status
- CPU
- Memory

---

# Stop a Task

```bash
aws ecs stop-task \
--cluster production-cluster \
--task task-id
```

---

# Task Lifecycle

```text
Provisioning

↓

Pending

↓

Running

↓

Stopping

↓

Stopped
```

---

# What is an ECS Service?

A Service maintains the desired number of running Tasks.

Example:

```text
Desired Tasks

↓

3
```

If one Task fails:

```text
Running

↓

2

↓

Service

↓

Launch New Task

↓

3
```

---

# Service Architecture

```text
Service

↓

Task

↓

Task

↓

Task
```

---

# Create a Service

```bash
aws ecs create-service \
--cluster production-cluster \
--service-name web-service \
--task-definition web-app \
--desired-count 3
```

---

# List Services

```bash
aws ecs list-services \
--cluster production-cluster
```

---

# Describe Service

```bash
aws ecs describe-services \
--cluster production-cluster \
--services web-service
```

Returns:

- Desired Count
- Running Count
- Pending Count
- Deployment Status
- Task Definition

---

# Update Service

Deploy a new Task Definition.

```bash
aws ecs update-service \
--cluster production-cluster \
--service web-service \
--task-definition web-app:2
```

A rolling deployment begins automatically.

---

# Scale a Service

Increase capacity.

```bash
aws ecs update-service \
--cluster production-cluster \
--service web-service \
--desired-count 5
```

Reduce capacity.

```bash
--desired-count 2
```

---

# Delete Service

```bash
aws ecs delete-service \
--cluster production-cluster \
--service web-service \
--force
```

---

# Desired Count

The Service always attempts to maintain the configured number of Tasks.

Example:

```text
Desired Count

↓

4

↓

Running

↓

4
```

---

# Essential Containers

A container marked:

```json
"essential": true
```

must remain healthy.

If it exits:

```text
Container Stops

↓

Task Stops

↓

Service Starts Replacement
```

---

# Multiple Containers

A Task can run multiple containers.

```text
Task

│

├── Web Container

├── Nginx

└── Fluent Bit
```

Containers share:

- Network
- Storage
- Lifecycle

---

# Common Errors

## ClusterNotFoundException

Verify:

- Cluster name
- Region
- AWS Account

---

## TaskDefinitionNotFoundException

Verify:

- Family name
- Revision
- Region

---

## ServiceNotFoundException

Verify:

- Service name
- Cluster

---

## RESOURCE:MEMORY

The cluster lacks available memory.

Solutions:

- Add capacity
- Increase Fargate limits
- Reduce Task memory

---

## RESOURCE:CPU

Not enough CPU capacity.

Review Task Definition resources.

---

# Production Best Practices

- Keep Task Definitions versioned.
- Never modify production revisions.
- Use Services instead of standalone Tasks for long-running applications.
- Keep Desired Count greater than one for production.
- Separate development and production clusters.
- Use meaningful Task Definition family names.
- Store Task Definitions in Git.
- Review unused revisions periodically.

---

# Real-World Workflow

```text
Build Docker Image

↓

Push to Amazon ECR

↓

Register Task Definition

↓

Create Service

↓

Run Tasks

↓

Production
```

---

# Architecture Note

```text
Amazon ECS Cluster
        │
        ▼
Service
        │
        ▼
Task Definition
        │
        ▼
Running Tasks
        │
        ▼
Containers
```

The Task Definition defines **how** containers should run, while the Service ensures the required number of Tasks are always running.

---

# Interview Note

### Question

**What is the difference between a Task Definition, a Task, and a Service in Amazon ECS?**

### Answer

A **Task Definition** is a versioned blueprint that defines how one or more containers should run, including the Docker image, CPU, memory, networking, IAM role, and environment variables. A **Task** is a running instance of a Task Definition. An **ECS Service** manages Tasks by maintaining the desired number of running instances, automatically replacing failed Tasks and performing rolling deployments when a new Task Definition revision is deployed.

---

# Key Takeaways

- Clusters provide the execution environment for ECS workloads.
- Task Definitions define container configuration and are immutable.
- Tasks are running instances of Task Definitions.
- Services maintain the desired number of running Tasks.
- Updating a Service with a new Task Definition triggers a rolling deployment.
- Task Definition revisions provide safe, versioned deployments.
- ECS Services are the preferred way to run long-lived production applications.