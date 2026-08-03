# Docker Lifecycle

## Overview

Every Docker Container goes through a well-defined lifecycle from creation to removal. Understanding this lifecycle is essential for managing containers effectively, designing reliable deployments, troubleshooting runtime issues, and building production-ready applications.

Although containers appear simple to start and stop, Docker performs several operations behind the scenes, including image lookup, writable layer creation, network configuration, volume mounting, process execution, and cleanup.

This chapter explains each stage of the Docker container lifecycle, the transitions between states, and best practices for managing containers throughout their lifecycle.

---

# What is the Docker Lifecycle?

The Docker Lifecycle describes the sequence of states a container passes through during its existence.

A container can be:

- Created
- Started
- Running
- Paused
- Restarted
- Stopped
- Removed

Each state represents a different stage of execution.

---

# Complete Lifecycle

```text
                Docker Image
                     │
                     ▼
                 Create
                     │
                     ▼
                  Created
                     │
                     ▼
                  Started
                     │
                     ▼
                  Running
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Paused    Restarting   Stopped
          │          │          │
          └──────────┼──────────┘
                     ▼
                  Removed
```

Every container follows this lifecycle until it is removed.

---

# Stage 1 — Image Selection

Everything begins with a Docker Image.

Example:

```text
python:3.12-slim
```

Docker checks whether the image exists locally.

If it is not available, Docker downloads it from a registry.

---

# Stage 2 — Container Creation

Docker creates a new container from the image.

During this stage Docker:

- Creates a writable layer
- Generates a unique Container ID
- Assigns metadata
- Prepares networking
- Prepares storage

At this point the application has **not** started.

State:

```text
Created
```

---

# Stage 3 — Container Startup

When the container starts, Docker performs several tasks.

```text
Container
      │
      ▼
Create Process
      │
      ▼
Assign Network
      │
      ▼
Mount Volumes
      │
      ▼
Apply Resource Limits
      │
      ▼
Execute ENTRYPOINT/CMD
```

The application's main process now begins execution.

---

# Stage 4 — Running

Once the main application starts successfully, the container enters the **Running** state.

Example:

```text
Running
```

During this stage Docker manages:

- Process execution
- Networking
- Storage
- Logs
- Resource limits
- Health checks

The container continues running while its main process remains active.

---

# Stage 5 — Pause

Docker can temporarily suspend container execution.

```text
Running
     │
     ▼
Paused
```

Characteristics:

- Processes stop executing
- Memory remains allocated
- Network configuration remains
- Filesystem remains unchanged

Pause is useful for temporary suspension without stopping the application.

---

# Stage 6 — Restart

If configured, Docker can automatically restart a container.

Typical causes include:

- Application crash
- Host reboot
- Restart policy
- Manual restart

Workflow:

```text
Running
     │
Application Exit
     │
     ▼
Restart Policy
     │
     ▼
Restarting
     │
     ▼
Running
```

---

# Restart Policies

Docker supports several restart policies.

| Policy | Description |
|----------|-------------|
| no | Never restart |
| on-failure | Restart only if the application exits with an error |
| unless-stopped | Restart unless manually stopped |
| always | Always restart |

Production systems commonly use restart policies to improve availability.

---

# Stage 7 — Stopped

A container enters the **Stopped** state when:

- The application exits
- A user stops it
- The host shuts down
- A fatal error occurs

The container still exists.

Only the application process has stopped.

Metadata, logs, and configuration remain available.

---

# Stage 8 — Removal

Removing a container deletes:

- Writable layer
- Metadata
- Network configuration
- Temporary filesystem

Persistent volumes remain unless explicitly removed.

Workflow:

```text
Stopped
     │
     ▼
Removed
```

Once removed, the container cannot be restarted.

---

# Container State Diagram

```text
Created
   │
   ▼
Running
 │  │
 │  ├────────► Paused
 │  │              │
 │  ▼              ▼
Restarting     Running
 │
 ▼
Stopped
 │
 ▼
Removed
```

Docker maintains these state transitions internally.

---

# Behind the Scenes

When Docker starts a container:

```text
Docker Image
      │
      ▼
Create Writable Layer
      │
      ▼
Assign Network
      │
      ▼
Mount Volumes
      │
      ▼
Apply Resource Limits
      │
      ▼
Launch Process
      │
      ▼
Running Container
```

Each step is managed automatically by Docker Engine.

---

# Container Exit

A container exits when its primary process terminates.

Example:

```text
Python Script
      │
      ▼
Script Completes
      │
      ▼
Container Stops
```

Unlike traditional servers, Docker containers are tied to the lifecycle of their main process.

---

# Ephemeral Containers

Docker containers are designed to be **ephemeral**.

This means they can be:

- Created quickly
- Destroyed safely
- Recreated consistently

Applications should avoid storing permanent data inside containers.

Instead, use:

- Docker Volumes
- Cloud Storage
- Databases

---

# Lifecycle in Production

A production deployment often follows this pattern.

```text
Build Image
      │
      ▼
Push Registry
      │
      ▼
Deploy Container
      │
      ▼
Health Check
      │
      ▼
Running
      │
      ▼
Rolling Update
      │
      ▼
New Container
      │
      ▼
Old Container Removed
```

Modern orchestration platforms automate much of this lifecycle.

---

# Monitoring the Lifecycle

During the lifecycle, teams typically monitor:

- Container health
- CPU usage
- Memory usage
- Network traffic
- Restart count
- Logs
- Exit codes

Monitoring helps identify issues before they impact production.

---

# Common Misconceptions

### Removing a container deletes the image.

Incorrect.

The image remains available unless explicitly removed.

---

### Stopping a container removes it.

Incorrect.

A stopped container can usually be started again.

---

### Data inside a container is permanent.

Incorrect.

The writable layer is deleted when the container is removed.

Persistent data should be stored in Docker Volumes.

---

# Best Practices

- Treat containers as disposable.
- Store persistent data outside containers.
- Configure appropriate restart policies.
- Monitor container health.
- Use health checks in production.
- Avoid manually modifying running containers.
- Replace containers instead of patching them.
- Use immutable image versions for deployments.

---

# Related Topics

- Docker Images
- Docker Containers
- Docker Volumes
- Docker Networking
- Docker Engine
- Docker Best Practices

---

## Key Takeaways

- Every Docker container progresses through a predictable lifecycle from creation to removal.
- Docker automatically manages networking, storage, process execution, and resource allocation throughout the lifecycle.
- Containers are designed to be ephemeral, making external storage essential for persistent data.
- Restart policies, health checks, and monitoring improve application reliability in production.
- Understanding the Docker lifecycle is fundamental for deploying, operating, and troubleshooting containerized applications effectively.