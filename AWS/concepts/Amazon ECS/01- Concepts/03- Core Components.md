# ECS Core Components

# Overview

Amazon ECS consists of several core components that work together to deploy, manage, scale, and monitor containerized applications.

Understanding these components is essential because almost every ECS interview question revolves around them.

Core Components:

- Cluster
- Task Definition
- Task
- Service
- Container
- Scheduler
- ECS Agent

---

# ECS Cluster

## What is a Cluster?

A Cluster is a logical grouping of resources where ECS workloads run.

Think of it as:

```text
Kubernetes Cluster
=
ECS Cluster
```

The cluster itself does not run applications.

Instead, it provides a location where ECS can place workloads.

---

## Example

Production Cluster

- User Service
- Order Service
- Payment Service

Development Cluster

- Internal APIs
- Test Services

---

## Why Use Multiple Clusters?

Benefits:

- Environment isolation
- Security separation
- Resource management
- Easier operations

---

# Task Definition

## What is a Task Definition?

A Task Definition is a blueprint that tells ECS how to run containers.

Think:

```text
Dockerfile
    =
Build Instructions

Task Definition
    =
Runtime Instructions
```

---

## Information Stored

A task definition typically contains:

- Docker image
- CPU allocation
- Memory allocation
- Environment variables
- Secrets
- Port mappings
- Volumes
- Logging configuration

---

## Example

```json
{
  "family": "user-service",
  "cpu": "512",
  "memory": "1024"
}
```

---

## Revisioning

Task definitions are versioned.

Example:

```text
user-service:1
user-service:2
user-service:3
```

Benefits:

- Rollbacks
- Deployment tracking
- Configuration history

---

# Container

## What is a Container?

A container is the smallest runnable unit.

Example:

```text
FastAPI Application
       ↓
Docker Image
       ↓
Container
```

Containers contain:

- Application code
- Runtime
- Dependencies
- Configuration

---

# Task

## What is a Task?

A Task is a running instance of a Task Definition.

Example:

```text
Task Definition
       ↓
Run
       ↓
Task
```

---

## Kubernetes Comparison

```text
Task Definition → Task

Deployment → Pod
```

Conceptually similar.

---

## Multiple Tasks

One Task Definition can create many Tasks.

Example:

```text
Task Definition
       ↓
Task A
Task B
Task C
```

Useful for scaling.

---

# Service

## What is a Service?

A Service maintains the desired number of running tasks.

Example:

Desired Count:

```text
3
```

Running Tasks:

```text
3
```

---

## Failure Scenario

Task B crashes.

Result:

```text
Task A
Task C
```

Running Tasks = 2

ECS detects mismatch.

ECS launches:

```text
Task D
```

Final State:

```text
Task A
Task C
Task D
```

Running Tasks = 3

---

## Why Services Matter

Benefits:

- Self-healing
- Auto scaling
- High availability
- Load balancer integration

---

# Desired State Management

One of the most important ECS concepts.

Desired State:

```text
3 Tasks
```

Current State:

```text
2 Tasks
```

ECS Scheduler detects drift.

Action:

```text
Launch New Task
```

Goal:

```text
Current State = Desired State
```

---

# ECS Scheduler

## What is the Scheduler?

The Scheduler is responsible for deciding:

- Where tasks run
- When tasks run
- Replacement decisions
- Scaling actions

---

## Scheduler Responsibilities

### Task Placement

Finds available capacity.

### Failure Recovery

Replaces failed tasks.

### Deployment Management

Controls rolling updates.

### Scaling

Adds or removes tasks.

---

# ECS Agent

## What is ECS Agent?

ECS Agent runs on ECS EC2 instances.

Responsibilities:

- Register instance
- Communicate with ECS
- Start containers
- Stop containers
- Report health status

---

## Communication Flow

ECS Control Plane
       ↓
ECS Agent
       ↓
Docker Runtime
       ↓
Container

---

# Task Lifecycle

Tasks move through several states.

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

## Provisioning

Resources allocated.

Examples:

- ENI creation
- Security group assignment

---

## Pending

Container image being pulled.

---

## Running

Application is active.

Traffic can be served.

---

## Stopping

Task is shutting down.

---

## Stopped

Task terminated.

---

# ECS Service Scheduler Example

Desired Count:

```text
5
```

Current Running:

```text
5
```

One task crashes.

Current Running:

```text
4
```

Scheduler action:

```text
Launch Replacement Task
```

Current Running:

```text
5
```

Self-healing complete.

---

# Production Example

FastAPI Service

Desired Count:

```text
4
```

Traffic increases.

CPU:

```text
80%
```

Auto Scaling triggers.

Result:

```text
4 → 8 Tasks
```

Traffic handled successfully.

---

# Common Interview Questions

## Difference Between Task and Task Definition?

Task Definition:

Blueprint.

Task:

Running instance.

---

## Difference Between Task and Service?

Task:

Single execution.

Service:

Maintains desired count.

---

## Why Use a Service Instead of Running Tasks Directly?

Services provide:

- Self-healing
- Scaling
- High availability

---

## What Happens When a Task Crashes?

Service detects failure.

Scheduler launches replacement.

---

# Common Mistakes

## Running Standalone Tasks

Problem:

No self-healing.

Solution:

Use Services.

---

## Large Monolithic Task Definitions

Problem:

Difficult scaling.

Solution:

Split into microservices.

---

## Hardcoding Secrets

Problem:

Security risk.

Solution:

Use Secrets Manager.

---

# Senior Engineer Perspective

Most engineers memorize ECS terminology.

Senior engineers understand:

- Desired state reconciliation
- Scheduler behavior
- Failure recovery
- Deployment workflows
- Scaling mechanisms

When troubleshooting ECS in production, these concepts become critical.

---

# Key Takeaways

- Cluster is a logical grouping of resources.
- Task Definition is a blueprint.
- Task is a running instance.
- Service maintains desired state.
- Scheduler controls placement and recovery.
- ECS Agent manages container execution.
- Services provide self-healing and high availability.
