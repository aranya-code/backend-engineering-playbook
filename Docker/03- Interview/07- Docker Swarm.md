# Docker Swarm

## Overview

Docker Swarm is Docker's native container orchestration platform that enables you to deploy, scale, and manage containerized applications across multiple Docker hosts. It transforms a group of Docker hosts into a single logical cluster, providing high availability, load balancing, service discovery, rolling updates, and fault tolerance.

Although Kubernetes has become the dominant orchestration platform, Docker Swarm remains an excellent interview topic because it demonstrates your understanding of clustering, orchestration, and distributed systems.

This section contains beginner to advanced Docker Swarm interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. What is Docker Swarm?

**Answer**

Docker Swarm is Docker's built-in orchestration platform used to manage multiple Docker hosts as a single cluster.

It provides:

- High Availability
- Service Discovery
- Load Balancing
- Scaling
- Rolling Updates
- Fault Tolerance

---

## 2. Why do we need Docker Swarm?

**Answer**

Docker Swarm helps manage applications across multiple servers.

Benefits include:

- High availability
- Automatic scheduling
- Easy scaling
- Fault tolerance
- Centralized cluster management

---

## 3. What is a Swarm Cluster?

**Answer**

A Swarm Cluster is a collection of Docker hosts (nodes) managed together as one logical system.

The cluster consists of:

- Manager Nodes
- Worker Nodes

---

## 4. What are Manager Nodes?

**Answer**

Manager nodes are responsible for:

- Cluster management
- Scheduling services
- Maintaining cluster state
- Leader election
- Worker management

---

## 5. What are Worker Nodes?

**Answer**

Worker nodes execute containers assigned by manager nodes.

They:

- Run application workloads
- Report status to managers
- Do not manage cluster configuration

---

## 6. How do you initialize a Swarm?

**Answer**

```bash
docker swarm init
```

---

## 7. How do you join a worker node?

**Answer**

```bash
docker swarm join \
--token <TOKEN> \
<MANAGER_IP>:2377
```

---

## 8. How do you list Swarm nodes?

**Answer**

```bash
docker node ls
```

---

## 9. How do you leave a Swarm?

**Answer**

```bash
docker swarm leave
```

Manager:

```bash
docker swarm leave --force
```

---

## 10. What is a Docker Service?

**Answer**

A Docker Service defines the desired state of an application running in the Swarm.

It specifies:

- Image
- Replicas
- Networks
- Ports
- Update strategy
- Placement constraints

---

# Intermediate Interview Questions

## 11. What is the difference between a container and a service?

**Answer**

| Container | Service |
|------------|----------|
| Single running instance | Desired application definition |
| Manually managed | Automatically managed by Swarm |
| Runs one process | Can manage multiple replicas |

---

## 12. How do you create a service?

**Answer**

```bash
docker service create nginx
```

---

## 13. How do you list services?

**Answer**

```bash
docker service ls
```

---

## 14. How do you inspect a service?

**Answer**

```bash
docker service inspect service_name
```

---

## 15. How do you scale a service?

**Answer**

```bash
docker service scale web=5
```

---

## 16. What is a replica?

**Answer**

A replica is one running instance of a service.

Example:

```text
Replicas: 5
```

means five identical containers are running.

---

## 17. What is a task?

**Answer**

A task is an individual container created by a service.

Each replica corresponds to one task.

---

## 18. What is routing mesh?

**Answer**

Routing mesh allows requests sent to any Swarm node to be automatically routed to an available service replica.

Benefits:

- Built-in load balancing
- No manual routing
- High availability

---

## 19. What network does Swarm use?

**Answer**

Swarm primarily uses:

- Overlay Network

for communication between containers running on different hosts.

---

## 20. What is service discovery?

**Answer**

Docker Swarm automatically provides DNS-based service discovery.

Applications communicate using service names rather than IP addresses.

---

# Advanced Interview Questions

## 21. How does leader election work?

**Answer**

Manager nodes elect one leader using the Raft consensus algorithm.

The leader manages:

- Scheduling
- Cluster updates
- State synchronization

---

## 22. Why should production clusters have an odd number of managers?

**Answer**

Raft requires a majority (quorum).

Common configurations:

- 3 managers
- 5 managers
- 7 managers

Odd numbers reduce split-brain scenarios.

---

## 23. What is quorum?

**Answer**

Quorum is the minimum number of manager nodes required to maintain cluster operations.

Example:

| Managers | Quorum |
|----------|---------|
| 3 | 2 |
| 5 | 3 |
| 7 | 4 |

---

## 24. What are rolling updates?

**Answer**

Rolling updates replace containers gradually instead of all at once.

Benefits:

- Zero or minimal downtime
- Easy rollback
- Reduced deployment risk

---

## 25. How do you rollback a failed deployment?

**Answer**

```bash
docker service rollback service_name
```

---

# Scenario-Based Interview Questions

## 26. One worker node fails. What happens?

**Expected Answer**

Swarm detects the failure and schedules replacement tasks on healthy worker nodes if sufficient resources are available.

---

## 27. One manager node crashes. Does the cluster stop working?

**Expected Answer**

No.

As long as quorum is maintained, another manager continues managing the cluster.

---

## 28. Users report downtime during deployments. How would you solve this?

**Expected Answer**

Configure rolling updates.

Use health checks.

Avoid updating all replicas simultaneously.

---

## 29. A service has five replicas, but only three are running. What would you investigate?

**Expected Answer**

- Available worker resources
- Node availability
- Placement constraints
- Service logs
- Image pull failures
- Network issues

Useful commands:

```bash
docker service ps service_name
```

```bash
docker node ls
```

---

## 30. Multiple servers need to run the same application with automatic failover. Which Docker feature would you use?

**Answer**

Docker Swarm Services.

They provide:

- Replication
- Automatic scheduling
- High availability
- Self-healing

---

# Production-Level Questions

## 31. What are the advantages of Docker Swarm?

**Answer**

- Easy to configure
- Native Docker integration
- Built-in load balancing
- Rolling updates
- Service discovery
- High availability
- Automatic failover

---

## 32. Docker Swarm vs Kubernetes?

**Answer**

| Docker Swarm | Kubernetes |
|--------------|------------|
| Easier to learn | Steeper learning curve |
| Simpler architecture | More feature-rich |
| Native Docker integration | Vendor-neutral ecosystem |
| Suitable for small to medium clusters | Ideal for large-scale production systems |

---

## 33. When would you choose Docker Swarm?

**Answer**

Docker Swarm is a good choice for:

- Small to medium-sized clusters
- Internal applications
- Development environments
- Teams that need simple orchestration
- Organizations already invested in the Docker ecosystem

For large, complex, cloud-native platforms, Kubernetes is generally the preferred orchestration solution.

---

# Interview Tips

- Understand the difference between **containers**, **services**, and **tasks**.
- Know the responsibilities of manager and worker nodes.
- Be able to explain Raft, quorum, and leader election at a high level.
- Understand routing mesh, overlay networking, and rolling updates.
- Expect comparisons between Docker Swarm and Kubernetes.

---

## Key Takeaways

- Docker Swarm is Docker's native orchestration platform for managing container clusters.
- Manager nodes control the cluster, while worker nodes execute application workloads.
- Services define the desired state of an application and can be scaled using replicas.
- Swarm provides built-in service discovery, overlay networking, load balancing, rolling updates, and self-healing capabilities.
- Although Kubernetes dominates large-scale orchestration, Docker Swarm remains an important interview topic for understanding distributed container management.