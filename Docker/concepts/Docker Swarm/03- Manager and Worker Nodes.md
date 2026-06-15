# Manager and Worker Nodes

## Overview

Docker Swarm clusters are built using two types of nodes:

1. **Manager Nodes**
2. **Worker Nodes**

Every node in a swarm runs the Docker Engine, but their responsibilities differ.

Understanding managers and workers is one of the most important Docker Swarm topics because it forms the foundation of cluster operations, scheduling, high availability, and fault tolerance.

---

# What is a Node?

A node is a machine participating in a Docker Swarm cluster.

A node can be:

- Physical Server
- Virtual Machine
- Cloud Instance
- Local Machine (Lab Environment)

Example:

```text
Swarm Cluster

Manager
Worker 1
Worker 2
Worker 3
```

Each machine is called a node.

---

# Node Types

Docker Swarm supports two node roles:

| Node Type | Purpose |
|------------|-----------|
| Manager | Controls the cluster |
| Worker | Executes workloads |

---

# Cluster Architecture

```text
                    Manager

                        │

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

    Worker 1       Worker 2       Worker 3

        │               │               │

        ▼               ▼               ▼

    Containers      Containers      Containers
```

---

# Manager Nodes

## Definition

A Manager Node is responsible for controlling and maintaining the swarm cluster.

Managers form the Control Plane of Docker Swarm.

Think of managers as the "brains" of the cluster.

---

# Responsibilities of Manager Nodes

Managers perform several critical functions.

---

## 1. Cluster Management

Managers maintain the overall state of the cluster.

Responsibilities include:

- Node registration
- Node removal
- Cluster health monitoring
- Configuration management

Example:

```bash
docker node ls
```

Only managers can execute this command.

---

## 2. Scheduling Tasks

Managers decide where containers should run.

Example:

```text
Web Service
Replicas = 3
```

Manager determines:

```text
Worker 1 → Container 1
Worker 2 → Container 2
Worker 3 → Container 3
```

This process is called scheduling.

---

## 3. Maintaining Desired State

Managers continuously compare:

```text
Desired State
```

with

```text
Actual State
```

Example:

Desired:

```text
3 Containers
```

Actual:

```text
2 Containers
```

Manager automatically creates:

```text
1 New Container
```

to restore the desired state.

---

## 4. Service Management

Managers handle:

```bash
docker service create
docker service update
docker service scale
docker service rm
```

Workers cannot perform these operations.

---

## 5. Rolling Updates

Managers coordinate application updates.

Example:

```bash
docker service update \
--image nginx:latest web
```

Manager updates tasks gradually to avoid downtime.

---

## 6. Load Balancing

Managers maintain information used by:

```text
Routing Mesh
```

for traffic distribution.

---

## 7. Security and Certificates

Managers operate the internal Certificate Authority (CA).

Responsibilities:

- Node authentication
- TLS certificate issuance
- Certificate rotation

Every node receives a certificate when joining the cluster.

---

# Manager Components

```text
Manager Node

├── API Server
├── Scheduler
├── Orchestrator
├── Dispatcher
├── Raft Store
└── Certificate Authority
```

---

# Active vs Passive Managers

In a multi-manager cluster:

```text
Manager 1
Manager 2
Manager 3
```

only one manager acts as the leader.

---

## Leader Manager

Responsibilities:

- Makes cluster decisions
- Writes cluster state
- Coordinates scheduling

---

## Follower Managers

Responsibilities:

- Maintain synchronized state
- Participate in elections
- Take over if leader fails

---

# Example

```text
Manager 1 → Leader

Manager 2 → Follower

Manager 3 → Follower
```

---

# Worker Nodes

## Definition

Worker Nodes execute application workloads assigned by managers.

Workers form the Data Plane of Docker Swarm.

Think of workers as the "muscles" of the cluster.

---

# Responsibilities of Worker Nodes

Workers perform execution-related tasks.

---

## 1. Run Containers

Primary responsibility:

```text
Execute Tasks
```

Example:

```text
Task
   │
   ▼
Container
```

Workers run these containers.

---

## 2. Receive Assignments

Managers assign tasks.

Example:

```text
Manager
   │
Assign Task
   │
   ▼
Worker
```

Worker starts the container.

---

## 3. Report Status

Workers continuously report:

- Task health
- Container state
- Resource usage

back to managers.

---

## 4. Maintain Networking

Workers participate in:

- Overlay networks
- Service discovery
- Routing mesh

---

# Worker Workflow

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

Monitor Container

    │

    ▼

Report Status

    │

    ▼

Manager
```

---

# Manager vs Worker

| Feature | Manager | Worker |
|----------|----------|----------|
| Controls Cluster | Yes | No |
| Schedules Tasks | Yes | No |
| Executes Containers | Yes* | Yes |
| Maintains State | Yes | No |
| Leader Election | Yes | No |
| Service Creation | Yes | No |
| Receives Tasks | Yes | Yes |

\* Managers can run containers unless configured otherwise.

---

# Manager as Worker

By default:

```text
Manager = Manager + Worker
```

Managers can execute workloads.

Example:

```text
Manager
 ├── Cluster Management
 └── Containers
```

---

# Why Avoid Workloads on Managers?

Production best practice:

```text
Managers = Control Plane

Workers = Workloads
```

Reason:

Heavy workloads can impact:

- Scheduling
- Cluster health
- Leader elections
- Performance

---

# Drain Manager Nodes

To prevent managers from running containers:

```bash
docker node update \
--availability drain manager1
```

Now:

```text
Manager
   │
Control Plane Only
```

No workloads scheduled.

---

# Node Availability States

Docker Swarm supports three availability modes.

---

# Active

Default state.

Node accepts tasks.

```text
Availability = Active
```

---

# Pause

Node does not receive new tasks.

Existing tasks continue running.

```bash
docker node update \
--availability pause worker1
```

---

# Drain

Node stops accepting tasks.

Existing tasks are moved elsewhere.

```bash
docker node update \
--availability drain worker1
```

Useful during maintenance.

---

# Viewing Nodes

List nodes:

```bash
docker node ls
```

Example:

```text
ID        HOSTNAME    STATUS   AVAILABILITY
abc123    manager     Ready    Active
def456    worker1     Ready    Active
ghi789    worker2     Ready    Active
```

---

# Inspecting a Node

```bash
docker node inspect worker1
```

Pretty output:

```bash
docker node inspect worker1 --pretty
```

---

# Promote Worker to Manager

Workers can be promoted.

Example:

```bash
docker node promote worker1
```

Result:

```text
Worker → Manager
```

---

# Demote Manager to Worker

```bash
docker node demote manager2
```

Result:

```text
Manager → Worker
```

---

# Remove a Node

First drain:

```bash
docker node update \
--availability drain worker1
```

Then remove:

```bash
docker node rm worker1
```

---

# Node Failure Scenario

Cluster:

```text
Manager

Worker 1
Worker 2
Worker 3
```

Service:

```text
Replicas = 3
```

Distribution:

```text
Worker 1 → Container A
Worker 2 → Container B
Worker 3 → Container C
```

---

# Worker Failure

```text
Worker 2 ❌
```

Manager detects:

```text
Container B Lost
```

Automatically creates:

```text
Container B
```

on another worker.

This is called:

```text
Self-Healing
```

---

# Manager Failure

Cluster:

```text
Manager 1 (Leader)

Manager 2 (Follower)

Manager 3 (Follower)
```

---

## Leader Failure

```text
Manager 1 ❌
```

Remaining managers vote.

Result:

```text
Manager 2 → New Leader
```

Cluster continues functioning.

---

# Recommended Production Setup

Small Production Cluster:

```text
Manager 1
Manager 2
Manager 3

Worker 1
Worker 2
Worker 3
```

Benefits:

- High Availability
- Quorum Support
- Fault Tolerance

---

# Best Practices

## Use Odd Number of Managers

Good:

```text
1
3
5
7
```

Bad:

```text
2
4
6
```

---

## Drain Managers

```bash
docker node update \
--availability drain manager1
```

Keep managers dedicated to cluster control.

---

## Use Multiple Workers

Avoid:

```text
Single Worker
```

Use:

```text
Multiple Workers
```

for fault tolerance.

---

## Monitor Node Health

Regularly check:

```bash
docker node ls
```

---

# Common Interview Questions

## What is a Manager Node?

A Manager Node controls the swarm cluster, schedules tasks, maintains desired state, handles leader elections, and manages services.

---

## What is a Worker Node?

A Worker Node executes containers and reports task status back to manager nodes.

---

## Can a Manager Run Containers?

Yes. By default, managers can run workloads, although production environments often drain managers to dedicate them to control-plane activities.

---

## What Happens if a Worker Fails?

The manager detects the failure and automatically schedules replacement tasks on healthy nodes.

---

## What Happens if a Manager Fails?

If multiple managers exist, Raft elects a new leader and cluster operations continue.

---

## Why Use Three Managers?

Three managers provide quorum and fault tolerance while minimizing resource usage.

---

## What is Drain Mode?

Drain mode prevents a node from receiving tasks and moves existing tasks to other nodes.

---

# Interview One-Liner

Manager nodes control and maintain the Docker Swarm cluster, while worker nodes execute application workloads. Together they provide orchestration, high availability, fault tolerance, and self-healing capabilities.