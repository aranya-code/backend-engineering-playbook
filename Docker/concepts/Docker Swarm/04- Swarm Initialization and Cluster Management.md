# Swarm Initialization and Cluster Management

## Overview

Before Docker hosts can work together as a cluster, Swarm Mode must be enabled.

This process involves:

1. Initializing the first Manager Node
2. Joining Worker Nodes
3. Adding Additional Managers
4. Managing Cluster Membership
5. Monitoring Cluster Health

This section covers the complete lifecycle of creating and managing a Docker Swarm cluster.

---

# What Happens During Swarm Initialization?

When you initialize a swarm:

```bash
docker swarm init
```

Docker performs several actions automatically:

- Creates a new Swarm Cluster
- Promotes the current node to Manager
- Generates cluster certificates
- Creates a Raft database
- Creates default overlay networks
- Generates join tokens

After initialization, the node becomes:

```text
Manager Node
```

and the cluster becomes:

```text
Swarm: Active
```

---

# Before Swarm Initialization

```text
Server 1

Docker Engine
```

Standalone Docker host.

No clustering.

---

# After Swarm Initialization

```text
Manager Node

└── Swarm Cluster
```

Now capable of accepting additional nodes.

---

# Initialize Swarm

## Basic Command

```bash
docker swarm init
```

Example Output:

```text
Swarm initialized:
current node (abc123) is now a manager.

To add a worker to this swarm:

docker swarm join \
--token SWMTKN-1-xxxxx \
192.168.1.10:2377
```

---

# Swarm Initialization Workflow

```text
docker swarm init
         │
         ▼
Create Swarm
         │
         ▼
Promote Node to Manager
         │
         ▼
Generate Certificates
         │
         ▼
Generate Join Tokens
         │
         ▼
Ready for Cluster Expansion
```

---

# Advertise Address

## Why It Matters

In multi-host environments, managers must advertise a reachable IP address.

Example:

```bash
docker swarm init \
--advertise-addr 192.168.1.10
```

---

## Architecture

```text
Manager

IP: 192.168.1.10

Workers connect here.
```

Without a proper advertise address, workers may fail to join.

---

# Verify Swarm Status

Check swarm status:

```bash
docker info
```

Look for:

```text
Swarm: active
```

Example:

```text
Swarm: active
 NodeID: abc123
 Is Manager: true
```

---

# Viewing Cluster Information

## List Nodes

```bash
docker node ls
```

Example:

```text
ID       HOSTNAME   STATUS   AVAILABILITY
abc123   manager    Ready    Active
```

---

# Join Tokens

## What are Join Tokens?

Join tokens are secure credentials used by nodes to join the cluster.

Docker generates:

1. Worker Token
2. Manager Token

---

# Retrieve Worker Token

```bash
docker swarm join-token worker
```

Example:

```text
docker swarm join \
--token SWMTKN-1-worker-token \
192.168.1.10:2377
```

---

# Retrieve Manager Token

```bash
docker swarm join-token manager
```

Example:

```text
docker swarm join \
--token SWMTKN-1-manager-token \
192.168.1.10:2377
```

---

# Worker vs Manager Join Tokens

| Token Type | Purpose |
|------------|----------|
| Worker Token | Join as Worker |
| Manager Token | Join as Manager |

---

# Adding Worker Nodes

## Step 1

Retrieve token:

```bash
docker swarm join-token worker
```

---

## Step 2

Run the join command on worker:

```bash
docker swarm join \
--token SWMTKN-1-xxxxx \
192.168.1.10:2377
```

Output:

```text
This node joined a swarm as a worker.
```

---

# Architecture After Worker Join

```text
Manager

   │

   ▼

Worker 1
```

---

# Adding Multiple Workers

Example:

```text
Manager

 ├── Worker 1
 ├── Worker 2
 └── Worker 3
```

All workers use the worker join token.

---

# Verify Worker Join

Run on manager:

```bash
docker node ls
```

Example:

```text
ID       HOSTNAME   STATUS
abc123   manager    Ready
def456   worker1    Ready
ghi789   worker2    Ready
```

---

# Adding Additional Managers

High Availability requires multiple managers.

---

## Step 1

Get manager token:

```bash
docker swarm join-token manager
```

---

## Step 2

Run join command:

```bash
docker swarm join \
--token SWMTKN-1-manager-token \
192.168.1.10:2377
```

Output:

```text
This node joined a swarm as a manager.
```

---

# Multi-Manager Architecture

```text
Manager 1 (Leader)

Manager 2 (Follower)

Manager 3 (Follower)
```

All managers participate in Raft consensus.

---

# Why Add Multiple Managers?

Benefits:

- High Availability
- Leader Election
- Fault Tolerance
- Quorum Protection

---

# Recommended Cluster Sizes

## Development Lab

```text
1 Manager
2 Workers
```

---

## Small Production

```text
3 Managers
3 Workers
```

---

## Medium Production

```text
3 Managers
5+ Workers
```

---

## Large Production

```text
5 Managers
Many Workers
```

---

# Promote Worker to Manager

Existing worker:

```text
worker1
```

Promote:

```bash
docker node promote worker1
```

Result:

```text
Worker → Manager
```

---

# Verify Promotion

```bash
docker node ls
```

Example:

```text
HOSTNAME   STATUS
manager1   Leader
worker1    Reachable
```

Worker is now a manager.

---

# Demote Manager to Worker

Example:

```bash
docker node demote manager2
```

Result:

```text
Manager → Worker
```

---

# Node Availability States

Docker Swarm supports:

```text
Active
Pause
Drain
```

---

# Active State

Default state.

```text
Availability = Active
```

Node accepts new tasks.

---

# Pause State

Node receives no new tasks.

Existing tasks continue running.

```bash
docker node update \
--availability pause worker1
```

---

# Drain State

Node stops receiving tasks.

Existing tasks are moved elsewhere.

```bash
docker node update \
--availability drain worker1
```

Useful during:

- Maintenance
- Upgrades
- Troubleshooting

---

# Drain Workflow

Before:

```text
Worker1

Task A
Task B
```

After:

```bash
docker node update \
--availability drain worker1
```

Result:

```text
Worker2

Task A
Task B
```

Tasks are migrated automatically.

---

# Inspect a Node

Detailed information:

```bash
docker node inspect worker1
```

Pretty output:

```bash
docker node inspect worker1 --pretty
```

---

# Remove a Node

## Step 1

Drain the node:

```bash
docker node update \
--availability drain worker1
```

---

## Step 2

Remove node:

```bash
docker node rm worker1
```

---

# Node Leaves Swarm

On worker:

```bash
docker swarm leave
```

Output:

```text
Node left the swarm.
```

---

# Manager Leaves Swarm

Managers require force:

```bash
docker swarm leave --force
```

---

# Why Force?

Managers participate in:

```text
Raft Consensus
```

Accidental removal could impact cluster health.

---

# Rotate Join Tokens

Security best practice:

Rotate tokens periodically.

---

## Rotate Worker Token

```bash
docker swarm join-token \
--rotate worker
```

---

## Rotate Manager Token

```bash
docker swarm join-token \
--rotate manager
```

---

# View Swarm Configuration

Inspect cluster:

```bash
docker swarm inspect
```

Pretty output:

```bash
docker swarm inspect --pretty
```

---

# Swarm Cluster Lifecycle

```text
Initialize Swarm
        │
        ▼
Create Manager
        │
        ▼
Join Workers
        │
        ▼
Join Managers
        │
        ▼
Deploy Services
        │
        ▼
Scale Applications
        │
        ▼
Maintain Cluster
```

---

# Common Cluster Commands

## Swarm

```bash
docker swarm init

docker swarm join

docker swarm leave

docker swarm leave --force

docker swarm inspect
```

---

## Tokens

```bash
docker swarm join-token worker

docker swarm join-token manager

docker swarm join-token --rotate worker

docker swarm join-token --rotate manager
```

---

## Nodes

```bash
docker node ls

docker node inspect

docker node promote

docker node demote

docker node rm

docker node update
```

---

# Real-World Example

Production Cluster:

```text
Manager 1 (Leader)

Manager 2 (Follower)

Manager 3 (Follower)

Worker 1
Worker 2
Worker 3
Worker 4
```

Benefits:

- High Availability
- Leader Election
- Automatic Recovery
- Zero-Downtime Maintenance

---

# Best Practices

## Use Odd Number of Managers

Good:

```text
3 Managers
5 Managers
7 Managers
```

Avoid:

```text
2 Managers
4 Managers
```

---

## Drain Before Maintenance

```bash
docker node update \
--availability drain worker1
```

---

## Rotate Join Tokens

```bash
docker swarm join-token --rotate
```

Regularly improve cluster security.

---

## Verify Cluster Health

```bash
docker node ls
```

Check frequently.

---

# Common Interview Questions

## What does `docker swarm init` do?

It initializes a new swarm cluster, promotes the current node to manager, creates cluster certificates, generates join tokens, and activates swarm mode.

---

## How do worker nodes join a swarm?

Using the worker join token generated by:

```bash
docker swarm join-token worker
```

---

## How do you add another manager?

Use the manager token:

```bash
docker swarm join-token manager
```

and join the node using the generated command.

---

## What is the difference between Pause and Drain?

Pause prevents new tasks from being scheduled, while Drain prevents new tasks and migrates existing tasks to other nodes.

---

## Why use three managers?

Three managers provide quorum and allow the cluster to tolerate one manager failure while maintaining availability.

---

# Interview One-Liner

Swarm initialization creates the first manager node and activates cluster mode, while cluster management involves adding nodes, maintaining quorum, managing node availability, and ensuring high availability across the swarm.