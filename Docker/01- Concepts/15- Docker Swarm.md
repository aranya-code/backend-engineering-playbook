# Docker Swarm

## Overview

Docker Swarm is Docker's native container orchestration platform. While Docker Engine manages containers on a single host, Docker Swarm extends Docker across multiple machines, allowing containers to be deployed, managed, scaled, and monitored as a unified cluster.

Swarm transforms a collection of Docker hosts into a single logical system. It provides built-in clustering, service discovery, load balancing, rolling updates, self-healing, and high availability without requiring external orchestration software.

Although Kubernetes has become the dominant orchestration platform, Docker Swarm remains an excellent choice for small-to-medium production environments due to its simplicity and seamless Docker integration.

---

# Why Docker Swarm?

Managing a few containers on a single machine is straightforward.

However, production systems often require:

- Multiple servers
- High availability
- Automatic failover
- Horizontal scaling
- Rolling updates
- Load balancing

Managing these manually quickly becomes impractical.

Docker Swarm automates these tasks.

---

# What is Docker Swarm?

Docker Swarm is Docker's built-in clustering and orchestration solution.

It allows multiple Docker hosts to operate as a single cluster.

Swarm provides:

- Cluster management
- Service orchestration
- Scheduling
- Automatic recovery
- Load balancing
- Secure communication
- Rolling deployments

---

# Docker Swarm Architecture

```text
                    Docker Swarm Cluster

                  +----------------------+
                  |    Manager Node      |
                  +----------+-----------+
                             |
        ---------------------------------------------
        |                    |                      |
        ▼                    ▼                      ▼
+---------------+    +---------------+    +---------------+
| Worker Node 1 |    | Worker Node 2 |    | Worker Node 3 |
+---------------+    +---------------+    +---------------+
        │                    │                      │
        ▼                    ▼                      ▼
  Containers          Containers           Containers
```

The Manager Node controls the cluster, while Worker Nodes execute application workloads.

---

# Swarm Components

Docker Swarm consists of several key components.

| Component | Responsibility |
|------------|----------------|
| Manager Node | Cluster management |
| Worker Node | Runs application containers |
| Service | Desired application state |
| Task | Individual container instance |
| Overlay Network | Multi-host networking |
| Ingress Network | Built-in load balancing |

---

# Manager Node

Manager Nodes control the cluster.

Responsibilities include:

- Scheduling containers
- Managing nodes
- Maintaining cluster state
- Service deployment
- Rolling updates
- Leader election

Manager Nodes do not need to run application workloads, although they can.

---

# Worker Node

Worker Nodes execute containers assigned by the manager.

Responsibilities:

- Run application containers
- Report health
- Execute tasks
- Receive scheduling instructions

Workers cannot modify cluster configuration.

---

# Service

A Service defines the desired state of an application.

Example:

```text
API Service

Desired Replicas: 5
```

Docker Swarm continuously attempts to maintain this desired state.

---

# Task

A Task represents one running container.

Example:

```text
API Service

├── Task 1
├── Task 2
├── Task 3
├── Task 4
└── Task 5
```

Each task runs one container.

---

# Cluster Architecture

```text id="8vh4t2"
                 Docker Swarm

              Manager Node
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 Worker 1      Worker 2     Worker 3
      │            │            │
      ▼            ▼            ▼
 Containers   Containers   Containers
```

Applications are distributed across multiple servers.

---

# Service Deployment Workflow

```text id="7jbfr3"
Application Image
        │
        ▼
Create Service
        │
        ▼
Manager Node
        │
        ▼
Schedule Tasks
        │
        ▼
Worker Nodes
        │
        ▼
Running Containers
```

The manager determines where each task should run.

---

# Scheduling

Docker Swarm automatically selects worker nodes based on:

- Resource availability
- Node status
- Scheduling constraints
- Cluster health

This eliminates manual placement decisions.

---

# Load Balancing

Swarm automatically distributes traffic across service replicas.

```text id="dhzvns"
              Client
                 │
                 ▼
          Routing Mesh
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 API 1       API 2       API 3
```

Requests are automatically routed to healthy containers.

---

# Service Discovery

Each service receives an internal DNS name.

Example:

```text id="s9o3z5"
database

redis

api
```

Containers communicate using service names instead of IP addresses.

---

# Overlay Network

Docker Swarm uses Overlay Networks for multi-host communication.

```text id="o6u6u5"
Host A
   │
   ▼
Overlay Network
   ▲
   │
Host B
   ▲
   │
Host C
```

Containers communicate securely across different servers.

---

# Self-Healing

If a container fails:

```text id="u9v3vc"
Running
   │
Failure
   │
   ▼
Manager Detects Failure
   │
   ▼
New Task Created
   │
   ▼
Application Restored
```

Swarm automatically restores the desired state.

---

# Rolling Updates

Swarm updates applications gradually.

```text id="8p3kgj"
Version 1

API 1
API 2
API 3

        │

Rolling Update

        ▼

Version 2

API 1
API 2
API 3
```

This minimizes downtime during deployments.

---

# High Availability

Multiple manager nodes improve fault tolerance.

```text id="8s1uxd"
        Manager 1
       /         \
      ▼           ▼
 Manager 2     Manager 3
```

If one manager fails, another manager can become the leader.

---

# Docker Swarm in Production

Typical architecture:

```text id="v25dtj"
                 Internet
                      │
                      ▼
               Load Balancer
                      │
                      ▼
             Docker Swarm Cluster
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     Worker 1    Worker 2    Worker 3
          │           │           │
          ▼           ▼           ▼
     API Containers API Containers API Containers
                      │
                      ▼
            PostgreSQL / Redis
```

Applications remain available even if individual servers fail.

---

# Advantages

Docker Swarm provides:

- Simple cluster management
- Native Docker integration
- High availability
- Built-in load balancing
- Rolling updates
- Self-healing
- Secure node communication
- Easy deployment

---

# Limitations

Docker Swarm has some limitations.

- Smaller ecosystem than Kubernetes
- Fewer advanced scheduling features
- Less flexible networking
- Smaller community adoption
- Limited extensibility

For very large enterprise environments, Kubernetes often provides greater flexibility.

---

# Docker Swarm vs Docker Compose

| Docker Compose | Docker Swarm |
|----------------|--------------|
| Single host | Multi-host cluster |
| Development | Production |
| No orchestration | Full orchestration |
| Manual scaling | Automatic scaling |
| No self-healing | Self-healing |
| No rolling updates | Rolling updates |

Compose manages applications.

Swarm orchestrates applications.

---

# Docker Swarm vs Kubernetes

| Docker Swarm | Kubernetes |
|---------------|------------|
| Easier to learn | More complex |
| Native Docker integration | Vendor-neutral ecosystem |
| Small to medium deployments | Large enterprise deployments |
| Faster setup | More features |
| Simpler management | Greater flexibility |

Both solve container orchestration but target different operational needs.

---

# Best Practices

- Deploy an odd number of manager nodes.
- Separate manager and worker responsibilities where possible.
- Use overlay networks for inter-node communication.
- Define resource limits for services.
- Configure health checks.
- Use rolling updates for deployments.
- Store persistent data outside containers.
- Monitor cluster health continuously.

---

# Related Topics

- Docker Compose
- Docker Networking
- Docker Volumes
- Docker Security
- Docker Best Practices

---

## Key Takeaways

- Docker Swarm extends Docker Engine into a clustered container orchestration platform.
- It introduces manager nodes, worker nodes, services, and tasks to automate deployment and lifecycle management.
- Swarm provides built-in load balancing, service discovery, rolling updates, self-healing, and high availability.
- Overlay networks enable secure communication between containers running on different hosts.
- Docker Swarm is well suited for organizations seeking a straightforward orchestration solution tightly integrated with Docker.