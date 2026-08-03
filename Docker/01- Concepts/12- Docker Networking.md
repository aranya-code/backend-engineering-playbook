# Docker Networking

## Overview

Docker Networking enables communication between containers, the host machine, and external systems. By default, every container is isolated, but Docker provides several networking drivers that allow containers to securely communicate while maintaining isolation.

Networking is one of Docker's most important features because nearly every real-world application consists of multiple services. For example, a web application may include an API server, database, cache, message broker, and reverse proxy, all running in separate containers that must communicate reliably.

This chapter explains Docker networking architecture, network drivers, communication models, DNS, service discovery, production networking, and best practices.

---

# Why Docker Networking?

Modern applications rarely consist of a single container.

Example:

```text
Browser
    │
    ▼
Nginx
    │
    ▼
Backend API
    │
 ┌──┴──────────┐
 ▼             ▼
Redis     PostgreSQL
```

Each service runs in a separate container.

Docker Networking enables secure communication between them.

---

# Docker Networking Architecture

```text
                 Docker Host

+--------------------------------------------------+
|                                                  |
|            Docker Network (Bridge)               |
|                                                  |
|   +-----------+    +-----------+    +----------+ |
|   |  API      |<-->|  Redis    |<-->|PostgreSQL| |
|   |Container  |    |Container  |    |Container | |
|   +-----------+    +-----------+    +----------+ |
|                                                  |
+--------------------------------------------------+
                 │
                 ▼
           Internet / Host
```

Every container connects to one or more Docker networks.

---

# Network Drivers

Docker supports multiple networking drivers.

| Driver | Typical Use Case |
|---------|------------------|
| Bridge | Single-host applications |
| Host | High-performance networking |
| Overlay | Multi-host clusters |
| None | Complete network isolation |
| Macvlan | Containers appear as physical devices |

Each driver serves different deployment scenarios.

---

# Bridge Network

The **Bridge Network** is Docker's default networking mode.

Characteristics:

- Single Docker host
- Internal container communication
- NAT to external networks
- Automatic DNS
- Isolated from other bridge networks

Most local development environments use the bridge driver.

---

# Bridge Network Architecture

```text
                  Docker Host

          +-----------------------+
          |    Bridge Network      |
          |                       |
          | API <--> Redis <--> DB|
          +-----------------------+
                    │
                    ▼
                 Internet
```

Containers connected to the same bridge network can communicate directly.

---

# Host Network

The Host network removes network isolation.

```text
Host Network

Application
     │
     ▼
Host Network Stack
```

Characteristics:

- No container network namespace
- Uses host ports directly
- Lower latency
- Higher performance

Typical use cases:

- Performance-sensitive workloads
- Monitoring agents
- Networking tools

---

# Overlay Network

Overlay networks connect containers running on multiple Docker hosts.

```text
Host A
  │
  ▼
Overlay Network
  ▲
  │
Host B
```

Commonly used with:

- Docker Swarm
- Multi-host deployments

Overlay networks provide seamless communication across servers.

---

# None Network

The None driver disables networking completely.

Characteristics:

- No external connectivity
- No Internet access
- No container communication

Useful for:

- Security-sensitive workloads
- Batch processing
- Offline tasks

---

# Macvlan Network

Macvlan allows containers to appear as physical devices on the network.

```text
Physical Network

      │
      ▼

Container A
Container B
Container C

Each has its own MAC address
```

Useful when applications require direct Layer 2 connectivity.

---

# Container Communication

Containers communicate through Docker Networks.

```text
API Container
      │
      ▼
Docker DNS
      │
      ▼
Database Container
```

Instead of IP addresses, Docker automatically resolves service names.

---

# Docker DNS

Every Docker network includes an internal DNS server.

Example:

```text
Database Host

db
```

Instead of:

```text
192.168.10.12
```

Advantages:

- Easier configuration
- Dynamic discovery
- No hardcoded IP addresses

---

# Service Discovery

Docker automatically provides service discovery.

Example:

```text
Application

DATABASE_HOST=db

REDIS_HOST=redis

CACHE_HOST=cache
```

Containers communicate using service names.

---

# Port Mapping

Containers have private networking.

To expose applications externally:

```text
Internet
     │
     ▼
Host Port
     │
     ▼
Container Port
```

Example:

```text
8080 → 80
```

External users connect to the host port.

---

# Internal vs External Communication

Internal:

```text
API
 │
 ▼
Database
```

External:

```text
Browser
   │
   ▼
Host
   │
   ▼
Container
```

Internal traffic stays within Docker networks.

External traffic enters through published ports.

---

# Multi-Container Application

Typical backend architecture:

```text
                 Internet
                     │
                     ▼
                  Nginx
                     │
                     ▼
               API Container
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 PostgreSQL Container      Redis Container
```

Each service communicates through Docker Networking.

---

# Network Isolation

Docker isolates applications by placing them on separate networks.

Example:

```text
Frontend Network

Frontend
    │
    ▼
API


Backend Network

API
 │
 ▼
Database
```

This limits unnecessary communication.

---

# Networking in Docker Compose

Docker Compose automatically creates a private network.

```text
Compose Project

api
 │
 ▼
database
 │
 ▼
redis
```

All services communicate using service names.

No manual network configuration is required for most projects.

---

# Networking in Docker Swarm

Docker Swarm primarily uses Overlay Networks.

```text
Host A
  │
  ▼
Overlay Network
  ▲
  │
Host B
  │
  ▼
Host C
```

This enables containers on different servers to communicate securely.

---

# Production Networking

Production deployments often include:

```text
                 Internet
                      │
                      ▼
               Load Balancer
                      │
                      ▼
               Reverse Proxy
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      API 1       API 2       API 3
          │
          ▼
     Private Network
          │
    ┌─────┴─────┐
    ▼           ▼
 Redis     PostgreSQL
```

Private backend services are typically inaccessible directly from the Internet.

---

# Security Considerations

Networking best practices include:

- Use private networks.
- Expose only required ports.
- Avoid unnecessary host networking.
- Segment frontend and backend services.
- Encrypt sensitive communication when appropriate.
- Apply firewall rules.
- Use network policies where supported.

---

# Common Misconceptions

### Containers communicate using localhost.

Incorrect.

`localhost` refers to the current container.

Containers should communicate using service names.

---

### Every container requires a public IP.

Incorrect.

Containers usually communicate over private Docker networks.

---

### Bridge networks work across multiple hosts.

Incorrect.

Bridge networks are limited to a single Docker host.

Multi-host communication requires an Overlay Network or another orchestration solution.

---

# Best Practices

- Use bridge networks for local development.
- Use overlay networks for clustered deployments.
- Communicate using service names instead of IP addresses.
- Expose only necessary ports.
- Separate frontend and backend networks.
- Avoid using the host network unless necessary.
- Keep databases on private networks.
- Monitor network traffic in production.

---

# Related Topics

- Docker Containers
- Docker Volumes
- Docker Compose
- Docker Swarm
- Docker Security
- Docker Best Practices

---

## Key Takeaways

- Docker Networking enables secure communication between containers, the host machine, and external systems.
- Docker supports multiple networking drivers, including Bridge, Host, Overlay, None, and Macvlan, each designed for different deployment scenarios.
- Containers should communicate using Docker's built-in DNS and service names rather than hardcoded IP addresses.
- Proper network segmentation, minimal port exposure, and private backend networks improve both security and maintainability.
- Understanding Docker Networking is essential for building scalable, secure, and production-ready multi-container applications.