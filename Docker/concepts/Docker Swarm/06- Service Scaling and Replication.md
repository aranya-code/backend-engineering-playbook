# Service Scaling and Replication

## Overview

One of the biggest advantages of Docker Swarm is its ability to automatically scale applications across multiple nodes.

Instead of manually creating containers:

```bash
docker run nginx
docker run nginx
docker run nginx
```

Swarm allows you to define the desired number of instances and automatically manages them.

```bash
docker service scale web=3
```

Docker Swarm creates, schedules, monitors, and replaces containers as needed.

---

# What is Scaling?

## Definition

Scaling is the process of increasing or decreasing the number of application instances running in a cluster.

The goal is to:

- Handle more traffic
- Improve availability
- Increase fault tolerance
- Optimize resource usage

---

# Types of Scaling

## Vertical Scaling

Increase resources of a single server.

Example:

```text
2 CPU → 8 CPU

4 GB RAM → 16 GB RAM
```

Architecture:

```text
Single Server

More CPU
More RAM
More Storage
```

Limitations:

- Hardware limits
- Single point of failure

---

## Horizontal Scaling

Add more application instances.

Architecture:

```text
Web App

Replica 1
Replica 2
Replica 3
Replica 4
```

Benefits:

- Better availability
- Better fault tolerance
- Easier growth

Docker Swarm primarily uses:

```text
Horizontal Scaling
```

---

# What is Replication?

## Definition

Replication means running multiple copies of the same application.

Example:

```text
Nginx

Replica 1
Replica 2
Replica 3
```

Each replica serves requests independently.

---

# Why Replication Matters

Without replication:

```text
1 Container
     │
     ▼
Failure
     │
     ▼
Application Down
```

With replication:

```text
Replica 1
Replica 2
Replica 3

One Fails
     │
     ▼
Others Continue Running
```

---

# Desired State and Replication

Swarm continuously maintains:

```text
Desired State
```

Example:

```text
Web Service

Replicas = 3
```

Desired:

```text
3 Running Tasks
```

---

# Current State

```text
Task 1 Running
Task 2 Running
Task 3 Running
```

Desired state achieved.

---

# Failure Scenario

```text
Task 2 Crashes
```

Current:

```text
Task 1 Running
Task 3 Running
```

Actual:

```text
2 Tasks
```

Desired:

```text
3 Tasks
```

---

# Swarm Response

Manager detects:

```text
Desired = 3
Actual = 2
```

Automatically creates:

```text
Task 4
```

Result:

```text
3 Running Tasks
```

This behavior is called:

```text
Self-Healing
```

---

# Replicated Services

## Definition

Replicated mode allows administrators to specify the exact number of replicas.

Example:

```bash
docker service create \
--name web \
--replicas 3 \
nginx
```

---

# Architecture

```text
Web Service

Replicas = 3

      │

 ┌────┼────┐

 ▼    ▼    ▼

T1   T2   T3

 │    │    │

 ▼    ▼    ▼

C1   C2   C3
```

---

# Verify Replicas

```bash
docker service ls
```

Example:

```text
NAME   MODE        REPLICAS
web    replicated  3/3
```

---

# Viewing Replica Distribution

```bash
docker service ps web
```

Example:

```text
NAME    NODE
web.1   worker1
web.2   worker2
web.3   worker3
```

---

# Scaling a Service

## Increase Replicas

Current:

```text
Replicas = 3
```

Scale:

```bash
docker service scale web=5
```

---

# Result

Swarm creates:

```text
Task 4
Task 5
```

New state:

```text
5 Running Tasks
```

---

# Architecture

Before:

```text
3 Replicas
```

After:

```text
5 Replicas
```

```text
      Web Service

            │

 ┌──────────┼──────────┐

 ▼          ▼          ▼

W1         W2         W3

 │          │          │

 ▼          ▼          ▼

2 Tasks    2 Tasks    1 Task
```

---

# Scaling Down

Current:

```text
Replicas = 5
```

Scale:

```bash
docker service scale web=2
```

Swarm removes:

```text
3 Tasks
```

Remaining:

```text
2 Running Tasks
```

---

# Alternative Scaling Method

Using update:

```bash
docker service update \
--replicas 5 \
web
```

Equivalent to:

```bash
docker service scale web=5
```

---

# Global Services

## Definition

Global services run one task on every node.

Unlike replicated mode, the number of replicas is not manually specified.

---

# Example

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

# Architecture

```text
Global Service

      │

 ┌────┼────┐

 ▼    ▼    ▼

W1   W2   W3

 │    │    │

 ▼    ▼    ▼

T1   T2   T3
```

---

# Automatic Scaling in Global Mode

Add node:

```text
Worker4
```

Swarm automatically creates:

```text
Task 4
```

No manual scaling required.

---

# Replicated vs Global Mode

| Feature | Replicated | Global |
|----------|-----------|---------|
| Replica Count | User Defined | One Per Node |
| Scaling | Manual | Automatic |
| Common Use | Applications | Agents |
| Example | Web Servers | Monitoring |

---

# Common Global Services

Examples:

```text
Prometheus Node Exporter

Fluentd

Log Collectors

Security Agents

Monitoring Agents
```

Because every node requires one instance.

---

# Load Balancing and Replication

When multiple replicas exist:

```text
Web Service

Replica 1
Replica 2
Replica 3
```

Traffic enters:

```text
Routing Mesh
```

and gets distributed.

---

# Example

```text
Client Requests

      │

      ▼

Routing Mesh

 ┌────┼────┐

 ▼    ▼    ▼

R1   R2   R3
```

Users don't need to know which replica serves the request.

---

# Placement During Scaling

Suppose:

```text
Workers

Worker1
Worker2
Worker3
```

Scale:

```text
Replicas = 6
```

Swarm scheduler attempts balanced placement:

```text
Worker1 → 2 Tasks

Worker2 → 2 Tasks

Worker3 → 2 Tasks
```

---

# Placement Constraints

Deploy only on workers:

```bash
docker service create \
--constraint node.role==worker \
--replicas 3 \
nginx
```

---

# Deploy Only on Managers

```bash
docker service create \
--constraint node.role==manager \
nginx
```

---

# Resource-Aware Scheduling

Swarm considers:

- Available CPU
- Available Memory
- Node Availability
- Constraints
- Existing Workloads

before scheduling tasks.

---

# Scaling Workflow

```text
Scale Request

      │

      ▼

Manager

      │

      ▼

Scheduler

      │

      ▼

Create Tasks

      │

      ▼

Assign Nodes

      │

      ▼

Start Containers
```

---

# Self-Healing During Scaling

Desired:

```text
Replicas = 5
```

Current:

```text
5 Running Tasks
```

---

# Node Failure

```text
Worker2 Fails
```

Tasks lost:

```text
2 Tasks
```

Current:

```text
3 Tasks
```

---

# Manager Response

Manager schedules replacements:

```text
Worker1

Worker3
```

Result:

```text
5 Running Tasks
```

Desired state restored.

---

# Inspect Service Scaling Configuration

```bash
docker service inspect web
```

Pretty output:

```bash
docker service inspect web --pretty
```

Look for:

```text
Mode: Replicated

Replicas: 5
```

---

# Real-World Example

E-Commerce Frontend

Initial deployment:

```bash
docker service create \
--name frontend \
--replicas 3 \
nginx
```

Traffic increases.

Scale:

```bash
docker service scale frontend=10
```

Result:

```text
10 Frontend Containers
```

distributed across the cluster.

No application redeployment required.

---

# Best Practices

## Always Use Multiple Replicas

Avoid:

```text
Replicas = 1
```

Use:

```text
Replicas = 2+
```

for fault tolerance.

---

## Use Global Mode for Node-Level Agents

Examples:

```text
Monitoring
Logging
Security
```

---

## Monitor Replica Health

```bash
docker service ps web
```

Regularly verify task status.

---

## Scale Gradually

Instead of:

```text
1 → 100
```

Prefer:

```text
1 → 5 → 10 → 20
```

to observe resource impact.

---

# Common Interview Questions

## What is Replication in Docker Swarm?

Replication is the process of running multiple copies of an application as tasks managed by a service.

---

## What is the Difference Between Scaling and Replication?

Replication refers to maintaining multiple copies of an application, while scaling refers to increasing or decreasing the number of replicas.

---

## What is Global Mode?

Global mode runs exactly one task on every available node in the cluster.

---

## What Happens When a Replica Fails?

Docker Swarm automatically creates a replacement task to maintain the service's desired state.

---

## How Do You Scale a Service?

Using:

```bash
docker service scale <service>=<replicas>
```

Example:

```bash
docker service scale web=5
```

---

# Interview One-Liner

Docker Swarm uses service replication and horizontal scaling to maintain application availability, distribute workloads across nodes, and automatically replace failed tasks to preserve the desired state.