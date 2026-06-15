# Services and Tasks

## Overview

In Docker Swarm, applications are not deployed as individual containers.

Instead, they are deployed as **Services**.

A Service defines the desired state of an application, while Docker Swarm creates and manages **Tasks** (containers) to maintain that state.

This is one of the most important concepts in Swarm because everything revolves around:

```text
Service
    │
    ▼
Tasks
    │
    ▼
Containers
```

Understanding this relationship is essential for scaling, updates, failover, and self-healing.

---

# Traditional Docker vs Docker Swarm

## Traditional Docker

Create a container directly:

```bash
docker run -d nginx
```

Architecture:

```text
docker run
     │
     ▼
 Container
```

Docker manages only that container.

---

## Docker Swarm

Create a service:

```bash
docker service create nginx
```

Architecture:

```text
Service
   │
   ▼
Tasks
   │
   ▼
Containers
```

Swarm manages the entire application lifecycle.

---

# What is a Service?

## Definition

A Service is the definition of an application's desired state within a swarm cluster.

It specifies:

- Container image
- Number of replicas
- Networks
- Ports
- Secrets
- Environment variables
- Placement rules

---

# Service Example

Create a service:

```bash
docker service create \
--name web \
nginx
```

Result:

```text
Service: web

Replicas: 1
Image: nginx
```

Swarm creates the container automatically.

---

# Service Architecture

```text
Service

  web

   │

   ▼

Task

   │

   ▼

Container
```

---

# Desired State

A service defines the desired state.

Example:

```text
Web Service

Replicas = 3
```

Desired state:

```text
3 Running Containers
```

Swarm continuously ensures this state exists.

---

# Service Components

A service contains:

```text
Service

├── Image
├── Replicas
├── Networks
├── Volumes
├── Secrets
├── Configurations
└── Update Policies
```

---

# Creating a Service

## Basic Service

```bash
docker service create nginx
```

Docker assigns a random service name.

---

## Named Service

```bash
docker service create \
--name web \
nginx
```

---

# Verify Service

List services:

```bash
docker service ls
```

Example:

```text
ID        NAME   MODE        REPLICAS
abc123    web    replicated  1/1
```

---

# What is a Task?

## Definition

A Task is the smallest scheduling unit in Docker Swarm.

A task represents a running container created by a service.

---

# Relationship

```text
Service
    │
    ▼
Task
    │
    ▼
Container
```

---

# Example

Service:

```text
Replicas = 3
```

Swarm creates:

```text
Task 1
Task 2
Task 3
```

Each task becomes:

```text
Container 1
Container 2
Container 3
```

---

# Service to Task Mapping

```text
Web Service

     │

 ┌───┼───┐

 ▼   ▼   ▼

T1  T2  T3

 │   │   │

 ▼   ▼   ▼

C1  C2  C3
```

---

# View Service Tasks

```bash
docker service ps web
```

Example:

```text
ID      NAME      NODE
abc     web.1     worker1
def     web.2     worker2
ghi     web.3     worker3
```

---

# Task Lifecycle

A task goes through several states.

```text
New
 │
 ▼
Assigned
 │
 ▼
Accepted
 │
 ▼
Preparing
 │
 ▼
Starting
 │
 ▼
Running
```

---

# Task Failure Lifecycle

```text
Running
    │
    ▼
Failed
    │
    ▼
Shutdown
    │
    ▼
Replacement Task Created
```

---

# Self-Healing

One of Swarm's most powerful features.

---

## Example

Desired State:

```text
3 Replicas
```

Current State:

```text
3 Running Tasks
```

---

## Failure

```text
Task 2 Crashes
```

Current:

```text
2 Running Tasks
```

---

## Swarm Response

```text
Desired = 3
Actual = 2
```

Manager creates:

```text
New Task
```

Result:

```text
3 Running Tasks
```

Desired state restored.

---

# Replicated Services

## Definition

Replicated mode allows administrators to specify the exact number of replicas.

---

## Example

```bash
docker service create \
--name web \
--replicas 3 \
nginx
```

Result:

```text
3 Tasks
```

distributed across nodes.

---

# Architecture

```text
Web Service

Replicas = 3

      │

 ┌────┼────┐

 ▼    ▼    ▼

W1   W2   W3
```

---

# Global Services

## Definition

Global mode runs one task on every available node.

---

## Example

```bash
docker service create \
--mode global \
nginx
```

---

# Cluster

```text
Worker1
Worker2
Worker3
```

Result:

```text
Worker1 → 1 Task

Worker2 → 1 Task

Worker3 → 1 Task
```

---

# Replicated vs Global

| Feature | Replicated | Global |
|-----------|-----------|---------|
| Number of Tasks | User Defined | One Per Node |
| Scaling | Manual | Automatic |
| Common Use | Applications | Monitoring Agents |

---

# Common Global Service Examples

```text
Prometheus Node Exporter

Log Collectors

Monitoring Agents

Security Agents
```

---

# Service Scaling

## Increase Replicas

Current:

```text
Replicas = 3
```

Scale:

```bash
docker service scale web=10
```

Result:

```text
10 Tasks
```

---

# Scale Down

Current:

```text
10 Tasks
```

Scale:

```bash
docker service scale web=3
```

Result:

```text
3 Tasks
```

---

# Inspect Service

Detailed service information:

```bash
docker service inspect web
```

---

## Pretty Output

```bash
docker service inspect web --pretty
```

---

# Service Placement

Swarm determines where tasks run.

Example:

```text
Worker1

Worker2

Worker3
```

Replicas:

```text
6
```

Possible placement:

```text
Worker1 → 2 Tasks

Worker2 → 2 Tasks

Worker3 → 2 Tasks
```

---

# Placement Constraints

Deploy only on manager:

```bash
docker service create \
--constraint node.role==manager \
nginx
```

---

# Deploy on Workers Only

```bash
docker service create \
--constraint node.role==worker \
nginx
```

---

# Service Networking

Create service on a network:

```bash
docker service create \
--network app-net \
nginx
```

Tasks automatically connect.

---

# Publish Ports

Expose service:

```bash
docker service create \
--name web \
--publish 80:80 \
nginx
```

Routing mesh distributes traffic.

---

# Service Updates

Update image:

```bash
docker service update \
--image nginx:latest \
web
```

Swarm performs rolling updates.

---

# Remove Service

Delete service:

```bash
docker service rm web
```

Result:

```text
Service Removed

Tasks Removed

Containers Removed
```

---

# Service Lifecycle

```text
Create Service
       │
       ▼
Schedule Tasks
       │
       ▼
Start Containers
       │
       ▼
Monitor Health
       │
       ▼
Scale / Update
       │
       ▼
Remove Service
```

---

# Service Discovery

Every service receives a DNS entry.

Example:

```text
frontend

backend

database
```

Applications communicate using:

```text
http://backend

http://database
```

instead of IP addresses.

---

# Real-World Example

E-Commerce Application:

```text
Frontend Service
Replicas = 3

Backend Service
Replicas = 2

Database Service
Replicas = 1
```

Architecture:

```text
Frontend

  │

  ▼

Backend

  │

  ▼

Database
```

Swarm maintains all services automatically.

---

# Important Commands

## Create Service

```bash
docker service create
```

---

## List Services

```bash
docker service ls
```

---

## View Tasks

```bash
docker service ps
```

---

## Inspect Service

```bash
docker service inspect
```

---

## Scale Service

```bash
docker service scale
```

---

## Update Service

```bash
docker service update
```

---

## Remove Service

```bash
docker service rm
```

---

# Best Practices

## Use Services Instead of Containers

Avoid:

```bash
docker run
```

Use:

```bash
docker service create
```

in swarm mode.

---

## Use Replicas

```bash
--replicas 3
```

for fault tolerance.

---

## Monitor Task Failures

Regularly check:

```bash
docker service ps
```

---

## Use Placement Constraints

Deploy workloads intentionally.

---

# Common Interview Questions

## What is a Service?

A Service is a definition of an application's desired state in Docker Swarm, including image, replicas, networking, and deployment configuration.

---

## What is a Task?

A Task is the smallest scheduling unit in Swarm and represents a running container created by a service.

---

## Difference Between Service and Container?

A Service defines what should run, while a Container is the actual running instance created by a Task.

---

## Difference Between Replicated and Global Services?

Replicated services run a user-defined number of tasks, while global services run exactly one task on every node.

---

## What Happens When a Task Fails?

Swarm automatically creates a replacement task to restore the service's desired state.

---

# Interview One-Liner

A Service defines the desired state of an application in Docker Swarm, while Tasks are the individual units of work that Swarm schedules and runs as containers to maintain that desired state.