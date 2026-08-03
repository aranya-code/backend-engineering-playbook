# Docker Swarm Issues

## Overview

Docker Swarm is Docker's native container orchestration platform that enables you to deploy, scale, and manage applications across multiple Docker hosts. While Swarm is relatively simple compared to Kubernetes, issues can still arise due to cluster configuration, node communication, networking, service deployment, leader election, and resource availability.

This guide covers the most common Docker Swarm issues, explains how to diagnose them, and provides practical solutions and preventive best practices.

---

## Common Docker Swarm Issues

| Issue | Severity |
|--------|----------|
| Swarm initialization failure | High |
| Worker node cannot join | High |
| Manager node unavailable | High |
| Service deployment failure | High |
| Tasks stuck in Pending state | High |
| Overlay network failure | High |
| Leader election problems | High |
| Node marked as Down | High |
| Service cannot communicate across nodes | High |
| Service update or rollback failure | Medium |

---

# Issue 1: Swarm Initialization Failure

## Symptoms

```text
Error response from daemon: could not initialize swarm
```

---

## Possible Causes

- Invalid advertise address.
- Network connectivity problems.
- Docker daemon not running.
- Firewall restrictions.

---

## How to Diagnose

Check Docker status:

```bash
docker info
```

Verify swarm status:

```bash
docker info | grep Swarm
```

---

## Solutions

Initialize using a valid IP:

```bash
docker swarm init --advertise-addr <MANAGER_IP>
```

Verify that Docker is running before initializing the cluster.

---

## Prevention

- Use static IP addresses for manager nodes.
- Verify network connectivity before creating the cluster.

---

# Issue 2: Worker Node Cannot Join the Swarm

## Symptoms

```text
Error response from daemon: rpc error
```

or

```text
connection timed out
```

---

## Possible Causes

- Incorrect join token.
- Firewall blocking required ports.
- Wrong manager IP.
- Manager node offline.

---

## How to Diagnose

View join tokens:

```bash
docker swarm join-token worker
```

Check manager nodes:

```bash
docker node ls
```

---

## Solutions

Generate a new join command:

```bash
docker swarm join-token worker
```

Run the generated command on the worker node.

Verify required ports are open.

---

## Prevention

- Store join tokens securely.
- Use reliable network connectivity between nodes.

---

# Issue 3: Manager Node Unavailable

## Symptoms

```text
This node is not a swarm manager.
```

---

## Possible Causes

- Manager failed.
- Swarm quorum lost.
- Node demoted accidentally.

---

## How to Diagnose

Check nodes:

```bash
docker node ls
```

Inspect node:

```bash
docker node inspect <NODE_NAME>
```

---

## Solutions

Promote another manager if available.

Recover failed manager.

Restore quorum.

---

## Prevention

- Always maintain an odd number of manager nodes.
- Use at least three managers in production.

---

# Issue 4: Service Deployment Failure

## Symptoms

```text
Rejected
```

or

```text
Pending
```

---

## Possible Causes

- Invalid image.
- Missing resources.
- Incorrect constraints.
- Network problems.

---

## How to Diagnose

View services:

```bash
docker service ls
```

Inspect service:

```bash
docker service inspect SERVICE_NAME
```

View tasks:

```bash
docker service ps SERVICE_NAME
```

---

## Solutions

Verify image exists.

Check placement constraints.

Ensure worker nodes have sufficient resources.

---

## Prevention

Validate service configuration before deployment.

---

# Issue 5: Tasks Stuck in Pending State

## Symptoms

```text
Pending
```

for long periods.

---

## Possible Causes

- No eligible worker.
- Resource constraints.
- Missing network.
- Invalid placement rules.

---

## How to Diagnose

Inspect service tasks:

```bash
docker service ps SERVICE_NAME
```

---

## Solutions

Increase available resources.

Modify placement constraints.

Verify overlay network.

---

## Prevention

Monitor cluster capacity.

---

# Issue 6: Overlay Network Failure

## Symptoms

Containers on different nodes cannot communicate.

---

## Possible Causes

- Firewall blocking VXLAN traffic.
- Overlay network corruption.
- Node communication failure.

---

## How to Diagnose

List networks:

```bash
docker network ls
```

Inspect overlay:

```bash
docker network inspect NETWORK_NAME
```

---

## Solutions

Recreate overlay network.

Verify ports:

- TCP 2377
- TCP/UDP 7946
- UDP 4789

---

## Prevention

Allow required ports through firewalls.

---

# Issue 7: Leader Election Problems

## Symptoms

Manager repeatedly changes leadership.

---

## Possible Causes

- Network instability.
- Manager node failure.
- Loss of quorum.

---

## How to Diagnose

View managers:

```bash
docker node ls
```

Review Docker logs.

---

## Solutions

Restore failed managers.

Improve network reliability.

Maintain quorum.

---

## Prevention

Deploy managers across reliable infrastructure.

---

# Issue 8: Node Status Down

## Symptoms

```text
STATUS: Down
```

---

## Possible Causes

- Node powered off.
- Docker daemon stopped.
- Network interruption.

---

## How to Diagnose

View cluster:

```bash
docker node ls
```

Check Docker:

```bash
systemctl status docker
```

---

## Solutions

Restart Docker.

Reconnect node.

Remove permanently failed nodes if necessary.

---

## Prevention

Monitor node health continuously.

---

# Issue 9: Services Cannot Communicate Across Nodes

## Symptoms

Inter-node requests fail.

---

## Possible Causes

- Overlay network failure.
- Firewall restrictions.
- Incorrect service configuration.

---

## How to Diagnose

Inspect overlay network:

```bash
docker network inspect NETWORK_NAME
```

Test connectivity between containers.

---

## Solutions

Reconnect services.

Verify overlay networking.

Restart affected services.

---

## Prevention

Use Docker's built-in DNS.

Avoid manual IP assignments.

---

# Issue 10: Service Update or Rollback Failure

## Symptoms

Rolling update fails.

Rollback never completes.

---

## Possible Causes

- Application startup failure.
- Health check failure.
- Invalid image.
- Resource shortage.

---

## How to Diagnose

View update status:

```bash
docker service ps SERVICE_NAME
```

Inspect service:

```bash
docker service inspect SERVICE_NAME
```

---

## Solutions

Rollback:

```bash
docker service rollback SERVICE_NAME
```

Deploy corrected image.

Verify health checks.

---

## Prevention

Test images before production rollout.

Use rolling updates with health checks.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| Initialize Swarm | `docker swarm init` |
| Join worker | `docker swarm join` |
| Leave swarm | `docker swarm leave` |
| List nodes | `docker node ls` |
| Inspect node | `docker node inspect` |
| List services | `docker service ls` |
| Inspect service | `docker service inspect` |
| View service tasks | `docker service ps` |
| Rollback service | `docker service rollback` |
| List overlay networks | `docker network ls` |

---

# Best Practices

- Deploy at least three manager nodes in production.
- Maintain an odd number of managers to preserve quorum.
- Monitor node health continuously.
- Use rolling updates with health checks.
- Test images before deployment.
- Open all required Swarm communication ports.
- Regularly back up Swarm state.
- Avoid running production clusters with a single manager.

---

# Related Topics

- Docker Swarm
- Docker Networking
- Docker Services
- Docker Stacks
- Docker Compose
- Docker CLI
- Container Networking Issues

---

## Key Takeaways

- Most Docker Swarm issues stem from cluster configuration, networking, node availability, or resource constraints.
- `docker node`, `docker service`, and `docker network` commands are the primary tools for diagnosing Swarm problems.
- Maintaining quorum, monitoring node health, and validating service configurations are essential for a stable cluster.
- Overlay networking requires proper firewall configuration and healthy node communication.
- Regular testing, monitoring, and controlled rolling updates help prevent production issues and simplify recovery.