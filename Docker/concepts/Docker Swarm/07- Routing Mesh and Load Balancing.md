# Routing Mesh and Load Balancing

## Overview

One of Docker Swarm's most powerful features is its built-in load balancing system called the **Routing Mesh**.

Routing Mesh allows a service to be accessible from **any node in the cluster**, regardless of where the actual container is running.

This means users do not need to know:

- Which node hosts the container
- Which replica serves the request
- Where the application is currently running

Docker Swarm automatically handles request routing and load balancing.

---

# Why Load Balancing is Needed

Imagine a service with three replicas.

```text
Web Service

Replica 1
Replica 2
Replica 3
```

Without load balancing:

```text
Client
  │
  ▼
Replica 1
```

Only one replica receives traffic.

This creates:

- Uneven workload
- Resource waste
- Potential bottlenecks

---

# With Load Balancing

```text
Client Requests

        │
        ▼

   Load Balancer

 ┌──────┼──────┐

 ▼      ▼      ▼

R1     R2     R3
```

Traffic is distributed across replicas.

---

# What is Routing Mesh?

## Definition

Routing Mesh is Docker Swarm's built-in ingress load balancing system.

It allows every node in the swarm to accept incoming requests for a service and forward them to the appropriate container.

---

# Key Concept

Every node participates in the routing mesh.

Example cluster:

```text
Manager
Worker1
Worker2
Worker3
```

Service:

```text
Web Service

Replicas = 3
```

Even if containers run only on:

```text
Worker1
Worker2
Worker3
```

Users can connect to:

```text
Manager

Worker1

Worker2

Worker3
```

using the same port.

---

# Routing Mesh Architecture

```text
                  Client

                     │

                     ▼

             Any Swarm Node

                     │

                     ▼

              Routing Mesh

                     │

      ┌──────────────┼──────────────┐

      ▼              ▼              ▼

 Replica 1      Replica 2      Replica 3
```

The client never interacts directly with individual containers.

---

# Publishing Ports

Routing Mesh works when ports are published.

---

## Example

```bash
docker service create \
--name web \
--publish 80:80 \
nginx
```

---

# Port Mapping

```text
Host Port       Container Port

80       --->        80
```

---

# Service Deployment Example

Create service:

```bash
docker service create \
--name web \
--replicas 3 \
--publish 80:80 \
nginx
```

Cluster:

```text
Manager

Worker1

Worker2

Worker3
```

---

# Replica Placement

```text
Worker1 → Replica 1

Worker2 → Replica 2

Worker3 → Replica 3
```

---

# Client Access

Users can access:

```text
http://manager:80

http://worker1:80

http://worker2:80

http://worker3:80
```

All requests reach the same service.

---

# How Routing Mesh Works

Suppose:

```text
Replica Running On

Worker2
```

User sends request to:

```text
Worker1
```

Request flow:

```text
Client

   │

   ▼

Worker1

   │

   ▼

Routing Mesh

   │

   ▼

Worker2

   │

   ▼

Container
```

Traffic is forwarded automatically.

---

# Real Example

Cluster:

```text
Worker1
Worker2
Worker3
```

Service:

```bash
docker service create \
--name web \
--replicas 3 \
--publish 8080:80 \
nginx
```

---

# Access

All these work:

```text
http://worker1:8080

http://worker2:8080

http://worker3:8080
```

Even if a specific node does not host a replica.

---

# Ingress Network

Routing Mesh relies on the special Docker network called:

```text
Ingress Network
```

---

# What is the Ingress Network?

A special overlay network automatically created when swarm mode is enabled.

Verify:

```bash
docker network ls
```

Example:

```text
NETWORK ID     NAME      DRIVER
abc123         ingress   overlay
```

---

# Purpose of Ingress Network

Provides:

- Service exposure
- Request routing
- Internal load balancing
- Cross-node communication

---

# Ingress Architecture

```text
Client

  │

  ▼

Ingress Network

  │

  ▼

Service Replicas
```

---

# Internal Load Balancing

Swarm performs load balancing between replicas.

---

## Example

Service:

```text
Replicas = 3
```

Requests:

```text
Request 1 → Replica 1

Request 2 → Replica 2

Request 3 → Replica 3

Request 4 → Replica 1
```

Traffic is distributed automatically.

---

# VIP (Virtual IP)

Every service receives a Virtual IP.

Example:

```text
Service Name: web

VIP: 10.0.0.5
```

Applications communicate with the VIP instead of individual containers.

---

# Service Discovery

Swarm provides DNS-based service discovery.

---

## Example

Services:

```text
frontend

backend

database
```

Communication:

```text
frontend → backend

backend → database
```

Using service names.

No hardcoded IPs required.

---

# Routing Mesh vs Traditional Load Balancer

## Traditional Architecture

```text
Internet

   │

   ▼

External Load Balancer

   │

   ▼

Application Servers
```

Requires separate infrastructure.

---

## Docker Swarm

```text
Internet

   │

   ▼

Routing Mesh

   │

   ▼

Containers
```

Built-in functionality.

---

# Host Mode Publishing

By default:

```text
Routing Mesh Enabled
```

---

## Example

```bash
docker service create \
--publish 80:80 \
nginx
```

Uses ingress mode.

---

# Host Mode

Disable routing mesh:

```bash
docker service create \
--publish mode=host,target=80,published=80 \
nginx
```

---

# Difference

### Ingress Mode

```text
Any Node

Can Accept Traffic
```

---

### Host Mode

```text
Only Node Hosting Container

Accepts Traffic
```

---

# Ingress vs Host Mode

| Feature | Ingress Mode | Host Mode |
|----------|-------------|------------|
| Routing Mesh | Yes | No |
| Accessible From Any Node | Yes | No |
| Built-In Load Balancing | Yes | No |
| Performance | Slightly Lower | Higher |
| Common Usage | Most Services | Specialized Cases |

---

# Load Balancing Example

Cluster:

```text
Worker1

Worker2

Worker3
```

Service:

```text
Replicas = 6
```

Distribution:

```text
Worker1 → 2 Replicas

Worker2 → 2 Replicas

Worker3 → 2 Replicas
```

---

# Request Flow

```text
Client

  │

  ▼

Routing Mesh

  │

  ▼

Any Available Replica
```

Swarm determines destination automatically.

---

# Node Failure Scenario

Before failure:

```text
Worker1 → Replica1

Worker2 → Replica2

Worker3 → Replica3
```

---

# Worker2 Fails

```text
Worker2 ❌
```

Replica2 lost.

---

# Swarm Response

Creates replacement:

```text
Worker1 → Replica4
```

Routing Mesh updates automatically.

Users continue accessing:

```text
http://service:80
```

without changes.

---

# Verify Published Ports

```bash
docker service ls
```

Example:

```text
NAME   PORTS

web    *:80->80/tcp
```

---

# Inspect Service Networking

```bash
docker service inspect web
```

Pretty:

```bash
docker service inspect web --pretty
```

---

# View Networks

```bash
docker network ls
```

---

# Inspect Ingress Network

```bash
docker network inspect ingress
```

---

# Common Commands

## Publish Port

```bash
docker service create \
--publish 80:80 \
nginx
```

---

## Multiple Ports

```bash
docker service create \
--publish 80:80 \
--publish 443:443 \
nginx
```

---

## Inspect Service

```bash
docker service inspect web
```

---

## View Networks

```bash
docker network ls
```

---

## Inspect Ingress

```bash
docker network inspect ingress
```

---

# Best Practices

## Use Routing Mesh for Most Applications

Default:

```text
Ingress Mode
```

is sufficient for most workloads.

---

## Use Multiple Replicas

```bash
--replicas 3
```

or more for effective load balancing.

---

## Monitor Service Health

```bash
docker service ps web
```

Regularly verify task status.

---

## Use Host Mode Only When Necessary

Examples:

- High-performance networking
- Specialized TCP workloads
- Port-sensitive applications

---

# Common Interview Questions

## What is Routing Mesh?

Routing Mesh is Docker Swarm's built-in load balancing system that allows any swarm node to receive traffic for a service and route it to an available replica.

---

## What is the Ingress Network?

The ingress network is a special overlay network automatically created by Docker Swarm to support routing mesh and service load balancing.

---

## Can I Access a Service from Any Node?

Yes. If the service uses ingress publishing mode, any swarm node can accept traffic and forward it to the correct container.

---

## What is the Difference Between Ingress and Host Mode?

Ingress mode uses routing mesh and load balancing, while host mode exposes ports only on nodes hosting the actual container.

---

## What is a VIP in Docker Swarm?

A Virtual IP assigned to a service that enables internal service discovery and load balancing between service replicas.

---

# Interview One-Liner

Docker Swarm Routing Mesh is a built-in ingress load balancing mechanism that allows any node in the cluster to receive requests and automatically route them to healthy service replicas using the ingress network and virtual IPs.