# Swarm Architecture

## Overview

Docker Swarm follows a distributed architecture where multiple Docker hosts work together as a single cluster.

The architecture is designed to provide:

- High Availability (HA)
- Fault Tolerance
- Scalability
- Load Balancing
- Service Discovery
- Automated Scheduling

Understanding the architecture is essential because almost every Docker Swarm interview question is based on how the components interact.

---

# Architecture Diagram

```text
                           Swarm Cluster

                    ┌─────────────────────┐
                    │   Manager Node      │
                    │     (Leader)        │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼

   Worker Node 1        Worker Node 2        Worker Node 3

         │                     │                     │

         ▼                     ▼                     ▼

      Tasks                 Tasks                 Tasks

         │                     │                     │

         ▼                     ▼                     ▼

    Containers           Containers           Containers
```

The entire cluster behaves like a single Docker Engine.

---

# Swarm Architecture Layers

Docker Swarm can be viewed as two major planes:

```text
Control Plane
      │
      ▼
Data Plane
```

---

# Control Plane

## Definition

The Control Plane is responsible for managing and maintaining the cluster.

Responsibilities include:

- Scheduling containers
- Managing services
- Monitoring nodes
- Cluster state management
- Leader election
- Scaling
- Rolling updates

The Control Plane exists on Manager Nodes.

---

## Control Plane Components

```text
Manager Node

├── Docker API
├── Scheduler
├── Orchestrator
├── Dispatcher
├── Certificate Authority
└── Raft Store
```

---

# Data Plane

## Definition

The Data Plane is responsible for running application workloads.

Responsibilities:

- Running containers
- Processing traffic
- Service communication
- Application execution

Worker Nodes participate primarily in the Data Plane.

---

# Manager Nodes

## Definition

Manager Nodes control the cluster.

Think of a manager node as the "brain" of Docker Swarm.

---

## Responsibilities

### Cluster Management

Maintains overall cluster health.

---

### Service Scheduling

Decides where containers should run.

---

### Scaling

Creates additional tasks when replicas increase.

---

### Failure Recovery

Detects failed nodes and reschedules tasks.

---

### State Management

Maintains desired state.

---

### Security

Issues certificates and manages node authentication.

---

# Manager Architecture

```text
Manager Node

 ├── API Server
 ├── Scheduler
 ├── Orchestrator
 ├── Dispatcher
 ├── Raft Database
 └── CA Service
```

---

# Scheduler

## Definition

The Scheduler decides where containers should run.

Example:

```text
Service = nginx
Replicas = 3
```

Scheduler determines:

```text
Replica 1 → Worker 1
Replica 2 → Worker 2
Replica 3 → Worker 3
```

---

# Orchestrator

## Definition

The Orchestrator maintains the desired state of the cluster.

Example:

Desired state:

```text
3 nginx containers
```

Actual state:

```text
2 nginx containers
```

Orchestrator automatically creates:

```text
1 new nginx container
```

to restore desired state.

---

# Dispatcher

## Definition

The Dispatcher communicates with worker nodes.

Responsibilities:

- Assign tasks
- Monitor workers
- Collect health information

---

# Certificate Authority (CA)

## Definition

Provides secure communication between swarm nodes.

Responsibilities:

- Node authentication
- Certificate issuance
- Certificate rotation

Every node receives a TLS certificate.

---

# Worker Nodes

## Definition

Worker Nodes execute tasks assigned by managers.

Think of workers as the "muscles" of the cluster.

---

## Responsibilities

### Execute Containers

Run workloads.

---

### Report Health

Send status information to managers.

---

### Receive Tasks

Accept scheduling decisions from managers.

---

## Worker Workflow

```text
Manager
   │
Assign Task
   │
   ▼
Worker
   │
Start Container
   │
   ▼
Report Status
   │
   ▼
Manager
```

---

# Service

## Definition

A Service is the desired state of an application.

Example:

```bash
docker service create \
--name web \
--replicas 3 \
nginx
```

Desired state:

```text
3 nginx containers
```

---

## Service Architecture

```text
Service
   │
   ├── Task 1
   ├── Task 2
   └── Task 3
```

---

# Task

## Definition

A Task is a single running container created by a service.

Example:

```text
Service
    │
    ▼
3 Replicas
    │
    ▼

Task 1
Task 2
Task 3
```

Each task corresponds to one container.

---

# Desired State

## Definition

Desired State is the configuration defined by the administrator.

Example:

```text
Web Service
Replicas = 5
```

Swarm continuously works to maintain:

```text
5 Running Containers
```

---

# Desired State Example

Current state:

```text
5 Containers
```

One container crashes:

```text
4 Containers
```

Swarm detects:

```text
Desired = 5
Actual = 4
```

Result:

```text
Launch New Container
```

Desired state restored.

---

# Swarm Scheduling

## What is Scheduling?

Scheduling is the process of selecting which node should run a task.

---

## Example

Cluster:

```text
Manager
Worker 1
Worker 2
Worker 3
```

Service:

```text
Replicas = 6
```

Scheduler distributes:

```text
Worker 1 → 2 Tasks
Worker 2 → 2 Tasks
Worker 3 → 2 Tasks
```

---

# Service Modes

Docker Swarm supports two scheduling modes.

---

## Replicated Mode

Administrator specifies the number of replicas.

Example:

```bash
docker service create \
--replicas 3 \
nginx
```

Result:

```text
3 Containers
```

distributed across nodes.

---

## Global Mode

One task runs on every node.

Example:

```bash
docker service create \
--mode global \
nginx
```

Cluster:

```text
Worker 1
Worker 2
Worker 3
```

Result:

```text
1 Container per Node
```

Total:

```text
3 Containers
```

---

# Routing Mesh

## Definition

Routing Mesh is Docker Swarm's built-in load-balancing system.

It allows any node to receive traffic for a service.

---

## Example

Service:

```bash
docker service create \
--name web \
--publish 80:80 \
nginx
```

Traffic:

```text
Client
   │
   ▼
Worker 2
```

Container might actually be running on:

```text
Worker 1
```

Routing Mesh forwards traffic automatically.

---

# Overlay Network

## Definition

Overlay Networks allow containers on different nodes to communicate.

---

## Example

```text
Worker 1
   │
frontend

Worker 2
   │
backend
```

Communication occurs over an overlay network.

---

# Raft Consensus

## Definition

Raft is the distributed consensus algorithm used by manager nodes.

Purpose:

- Maintain cluster state
- Elect leaders
- Handle failures

---

# Raft Architecture

```text
Manager 1 (Leader)

Manager 2 (Follower)

Manager 3 (Follower)
```

---

# Leader Election

If Leader fails:

```text
Manager 1 ❌
```

Remaining managers vote.

```text
Manager 2 → New Leader
```

Cluster continues operating.

---

# Quorum

## Definition

A majority of managers must be available.

Formula:

```text
(N / 2) + 1
```

Examples:

| Managers | Quorum Required |
|-----------|----------------|
| 1 | 1 |
| 3 | 2 |
| 5 | 3 |
| 7 | 4 |

---

# Why Odd Number of Managers?

Good:

```text
3 Managers
5 Managers
7 Managers
```

Bad:

```text
2 Managers
4 Managers
6 Managers
```

Odd numbers maximize fault tolerance while minimizing resources.

---

# Node Communication Flow

```text
User

 │

 ▼

Manager

 │

 ▼

Scheduler

 │

 ▼

Worker

 │

 ▼

Task

 │

 ▼

Container
```

---

# Self-Healing Architecture

Desired State:

```text
3 Replicas
```

Current State:

```text
2 Replicas
```

Swarm automatically:

```text
Detect Failure
      │
      ▼
Schedule New Task
      │
      ▼
Launch Container
```

Desired state restored.

---

# Complete Swarm Architecture

```text
                    Manager (Leader)

            ┌────────────┼────────────┐

            ▼            ▼            ▼

       Worker 1     Worker 2     Worker 3

            │            │            │

            ▼            ▼            ▼

       Container    Container    Container

            │            │            │

            └──── Overlay Network ────┘

                         │

                         ▼

                    Routing Mesh

                         │

                         ▼

                       Users
```

---

# Best Practices

### Use Multiple Managers

Production:

```text
3 Managers
```

Minimum recommended HA setup.

---

### Use Overlay Networks

```bash
docker network create \
--driver overlay app-net
```

---

### Use Replicated Services

```bash
docker service create \
--replicas 3 nginx
```

for fault tolerance.

---

### Monitor Manager Health

Managers are the control plane.

Manager failure impacts cluster operations.

---

# Common Interview Questions

### What is the difference between a Service and a Task?

A Service defines the desired state, while a Task is the actual running container created to satisfy that state.

---

### What is the Control Plane?

The Control Plane consists of manager nodes responsible for scheduling, orchestration, and maintaining cluster state.

---

### What is the Data Plane?

The Data Plane consists of worker nodes that execute application workloads.

---

### What is Desired State?

Desired State is the target configuration defined by the administrator that Swarm continuously attempts to maintain.

---

### Why does Swarm use Raft?

Raft provides leader election, fault tolerance, and consistent cluster state across manager nodes.

---

# Interview One-Liner

Docker Swarm architecture consists of manager nodes forming the control plane and worker nodes forming the data plane, working together through Raft consensus, service scheduling, overlay networking, and routing mesh to provide a highly available container orchestration platform.