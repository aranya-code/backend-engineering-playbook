# Docker Containers

## Overview

A Docker Container is a lightweight, isolated, executable instance of a Docker Image. While an image serves as a blueprint, a container is the running application created from that blueprint.

Containers package an application together with its runtime, dependencies, configuration, and filesystem, allowing the application to run consistently across different environments. They provide process isolation while sharing the host operating system's kernel, making them significantly more efficient than traditional virtual machines.

Containers are the core execution unit of Docker and are widely used in cloud-native applications, microservices, CI/CD pipelines, and production deployments.

---

# What is a Docker Container?

A Docker Container is a running instance of a Docker Image.

It contains:

- Application
- Runtime
- Libraries
- Dependencies
- Configuration
- Writable filesystem layer
- Isolated processes

Unlike images, containers execute applications.

---

# Image vs Container

The relationship between images and containers can be summarized as follows.

| Docker Image | Docker Container |
|--------------|------------------|
| Template | Running Instance |
| Immutable | Writable |
| Read-only | Read/Write Layer |
| Blueprint | Executing Application |
| Can Create Many Containers | Created From One Image |

One image can create multiple independent containers.

---

# Container Architecture

```text
                 Docker Image
                      │
                      ▼
          +-------------------------+
          |   Read-Only Image       |
          +-------------------------+
                      │
                      ▼
          +-------------------------+
          | Writable Container Layer|
          +-------------------------+
                      │
                      ▼
             Running Application
```

The writable layer stores changes made while the container is running.

---

# How Containers Work

When Docker starts a container:

1. Selects a Docker Image.
2. Creates a writable layer.
3. Allocates network resources.
4. Mounts required volumes.
5. Starts the application process.

The container continues running until its main process exits.

---

# Container Lifecycle

Containers move through several states.

```text
Create
   │
   ▼
Running
   │
   ├──────────────┐
   ▼              ▼
Paused         Restarting
   │              │
   ▼              ▼
Stopped <─────────┘
   │
   ▼
Removed
```

Each state represents a different stage in the container's lifecycle.

---

# Container States

## Created

Docker has created the container, but it has not yet started.

---

## Running

The application's main process is currently executing.

---

## Paused

Container processes are temporarily suspended without stopping the container.

---

## Restarting

Docker is attempting to restart the container after a failure or according to its restart policy.

---

## Stopped

The application has exited or the container has been stopped.

---

## Removed

The container has been deleted from the Docker host.

---

# Container Isolation

Docker isolates containers using Linux kernel features.

Each container has its own:

- Process namespace
- Network namespace
- Mount namespace
- Hostname
- Filesystem
- Environment variables

Although isolated, containers share the host operating system's kernel.

---

# Container Filesystem

Every container consists of:

```text
+----------------------------+
| Writable Layer             |
+----------------------------+
| Image Layer 3              |
+----------------------------+
| Image Layer 2              |
+----------------------------+
| Image Layer 1              |
+----------------------------+
```

The image layers remain read-only.

Only the top writable layer changes while the container is running.

---

# Writable Layer

Changes stored in the writable layer include:

- New files
- Modified files
- Temporary data
- Logs (unless redirected)
- Runtime changes

If the container is removed, the writable layer is removed as well.

Persistent data should therefore be stored in Docker Volumes.

---

# Container Networking

Every container can communicate using Docker Networks.

Typical communication:

```text
            Docker Network

     +-----------+     +-----------+
     | Container |-----| Container |
     |    API    |     | Database  |
     +-----------+     +-----------+
             │
             ▼
        Internet
```

Containers communicate using service names rather than IP addresses whenever possible.

---

# Container Storage

Containers should remain stateless whenever possible.

Persistent data should be stored in:

- Docker Volumes
- Bind Mounts
- Network Storage
- Cloud Storage

This ensures data survives container replacement.

---

# Container Resource Management

Docker can limit resources assigned to containers.

Examples include:

- CPU
- Memory
- Swap
- Process limits
- File descriptors

Resource limits help prevent a single container from exhausting host resources.

---

# Container Restart Policies

Docker supports automatic restart behavior.

Common policies include:

| Policy | Description |
|---------|-------------|
| no | Never restart |
| on-failure | Restart only after failures |
| unless-stopped | Restart unless explicitly stopped |
| always | Always restart |

Restart policies improve application availability.

---

# Multiple Containers

Modern applications usually consist of several containers.

Example:

```text
                 Internet
                     │
                     ▼
                  Nginx
                     │
                     ▼
               API Container
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
 PostgreSQL Container      Redis Container
```

Each container performs a single responsibility.

---

# Containers in Microservices

Each microservice typically runs inside its own container.

```text
                API Gateway
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 User Service   Product Service   Order Service
      │              │              │
      ▼              ▼              ▼
 PostgreSQL      MongoDB         Redis
```

This architecture allows independent deployment and scaling.

---

# Ephemeral Nature of Containers

Containers are designed to be **ephemeral**.

This means they can be:

- Created quickly
- Destroyed quickly
- Replaced easily
- Rebuilt consistently

Applications should avoid storing important data inside containers.

---

# Advantages of Containers

Containers provide:

- Lightweight execution
- Fast startup
- Environment consistency
- Application isolation
- Efficient resource utilization
- Easy deployment
- High portability
- Simple scaling

---

# Limitations

Containers also have some limitations.

- Share the host kernel
- Require external persistent storage
- Depend on proper security configuration
- Not suitable for every workload
- Require orchestration for large-scale deployments

---

# Common Misconceptions

### Containers are Virtual Machines.

Incorrect.

Containers share the host operating system's kernel and do not include a complete guest operating system.

---

### Containers permanently store application data.

Incorrect.

Container storage is temporary unless external storage such as Docker Volumes is used.

---

### Every container requires its own image.

Incorrect.

Multiple containers can share the same Docker Image.

---

# Best Practices

- Run one primary application per container.
- Treat containers as immutable and disposable.
- Store persistent data in Docker Volumes.
- Use health checks for production workloads.
- Run containers as non-root users.
- Keep containers lightweight.
- Monitor CPU, memory, and disk usage.
- Use restart policies where appropriate.

---

# Related Topics

- Docker Images
- Docker Lifecycle
- Docker Volumes
- Docker Networking
- Docker Security
- Docker Engine

---

## Key Takeaways

- Docker Containers are lightweight, isolated runtime instances created from Docker Images.
- Containers share the host operating system's kernel while maintaining isolated processes, filesystems, and networking.
- Each container includes a writable layer that stores runtime changes, making external volumes essential for persistent data.
- Containers are designed to be ephemeral, enabling rapid deployment, scaling, and replacement.
- Understanding container architecture and lifecycle is fundamental to building reliable, scalable, and production-ready containerized applications.