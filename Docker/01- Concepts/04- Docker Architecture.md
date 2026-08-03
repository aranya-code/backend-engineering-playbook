# Docker Architecture

## Overview

Docker follows a **client-server architecture** that separates user interactions from container management. Rather than interacting directly with containers, users communicate with the Docker Client, which sends requests to the Docker Daemon. The daemon is responsible for building images, creating containers, managing storage, configuring networking, and communicating with container registries.

Understanding Docker's architecture is essential because every Docker operation—from building an image to deploying a production application—passes through these architectural components.

---

# Why Docker Uses a Client-Server Architecture

Docker separates responsibilities into different components.

This provides:

- Better modularity
- Easier automation
- Remote management
- API integration
- Better scalability
- Platform independence

Instead of managing containers directly, users communicate with Docker through well-defined interfaces.

---

# High-Level Architecture

Docker consists of several major components working together.

```text
                    Docker Architecture

                +----------------------+
                |    Docker Client     |
                |    (docker CLI)      |
                +----------+-----------+
                           |
                           | Docker API
                           |
                +----------v-----------+
                |    Docker Daemon     |
                |      (dockerd)       |
                +----------+-----------+
                           |
      +--------------------+----------------------+
      |                    |                      |
      ▼                    ▼                      ▼
 Docker Images      Docker Containers      Docker Networks
                                               │
                                               ▼
                                         Docker Volumes

                           │
                           ▼
                    Docker Registry
```

---

# Major Components

Docker architecture consists of several core components.

| Component | Responsibility |
|-----------|----------------|
| Docker Client | Accepts user commands |
| Docker Daemon | Performs Docker operations |
| Docker Engine | Runtime platform |
| Docker Images | Read-only templates |
| Docker Containers | Running applications |
| Docker Registry | Stores Docker images |
| Docker Networks | Container communication |
| Docker Volumes | Persistent storage |

---

# Docker Client

The Docker Client is the interface users interact with.

Examples include:

```bash
docker run
```

```bash
docker build
```

```bash
docker pull
```

```bash
docker compose up
```

The client does not manage containers itself.

Instead, it sends requests to the Docker Daemon.

---

# Docker Daemon

The Docker Daemon (`dockerd`) is the heart of Docker.

It is responsible for:

- Building images
- Creating containers
- Starting containers
- Stopping containers
- Managing networks
- Managing volumes
- Pulling images
- Pushing images

Every Docker operation eventually reaches the daemon.

---

# Docker Engine

Docker Engine is the complete runtime platform.

It consists of:

- Docker Daemon
- Docker API
- Docker CLI

Together they provide everything needed to build and manage containers.

---

# Docker Images

Docker Images are immutable templates.

An image contains:

- Application code
- Runtime
- Libraries
- Dependencies
- Configuration
- Startup command

Images are used to create containers.

---

# Docker Containers

Containers are running instances of Docker images.

Each container has:

- Isolated processes
- Own filesystem
- Own network namespace
- Writable layer

Multiple containers can be created from the same image.

---

# Docker Registry

Docker images are stored in registries.

Examples include:

- Docker Hub
- Amazon ECR
- Azure Container Registry
- Google Artifact Registry
- GitHub Container Registry
- Harbor

Registries allow images to be shared across teams and environments.

---

# Docker Networks

Docker Networks enable communication between:

- Containers
- Host machine
- External systems

Common network drivers include:

- Bridge
- Host
- Overlay
- None
- Macvlan

Networking is covered in detail later in this playbook.

---

# Docker Volumes

Volumes provide persistent storage.

Unlike containers, volumes remain after containers are removed.

Typical use cases include:

- Databases
- Uploaded files
- Logs
- Shared storage

---

# Docker API

The Docker Client communicates with the Docker Daemon through the Docker REST API.

Communication typically occurs over:

Linux:

```text
/var/run/docker.sock
```

Windows:

```text
Named Pipe
```

Or via TCP when configured.

---

# Request Flow

Every Docker command follows a similar workflow.

Example:

```bash
docker run nginx
```

Workflow:

```text
User
 │
 ▼
Docker CLI
 │
 ▼
Docker API
 │
 ▼
Docker Daemon
 │
 ├── Check Local Image
 │
 ├── Pull Image (if needed)
 │
 ├── Create Container
 │
 ├── Configure Network
 │
 ├── Mount Volumes
 │
 └── Start Application
```

---

# Image Build Workflow

Building an image follows another workflow.

```text
Dockerfile
     │
     ▼
Docker Build
     │
     ▼
Image Layers
     │
     ▼
Docker Image
     │
     ▼
Registry (Optional)
```

Docker caches image layers to improve build performance.

---

# Container Creation Workflow

When a container starts:

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
Start Process
      │
      ▼
Running Container
```

Every container receives its own writable layer while sharing the underlying read-only image layers.

---

# Docker and Registries

When an image is unavailable locally:

```text
docker run nginx
        │
        ▼
Local Image Exists?
      │
 ┌────┴─────┐
 │          │
Yes         No
 │          │
 ▼          ▼
Run      Pull Image
              │
              ▼
       Docker Registry
              │
              ▼
        Store Locally
              │
              ▼
       Start Container
```

---

# Docker Architecture in Development

Typical development workflow:

```text
Developer
     │
     ▼
Write Dockerfile
     │
     ▼
Build Image
     │
     ▼
Run Container
     │
     ▼
Test Application
```

This allows developers to test applications in consistent environments.

---

# Docker Architecture in Production

A production deployment typically includes additional infrastructure.

```text
                 Internet
                      │
                      ▼
               Load Balancer
                      │
                      ▼
              Reverse Proxy
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Container 1   Container 2   Container 3
        │             │             │
        └─────────────┼─────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     PostgreSQL               Redis
```

Docker provides the runtime platform while additional services provide high availability, scalability, and reliability.

---

# Advantages of Docker Architecture

The architecture provides several benefits.

- Modular design
- API-driven automation
- Remote management
- Image portability
- Efficient resource utilization
- Easy scalability
- Platform independence
- Integration with orchestration platforms

---

# Common Misconceptions

### Docker CLI runs containers.

Incorrect.

The Docker CLI only sends commands.

The Docker Daemon performs the actual work.

---

### Docker Engine is only the daemon.

Incorrect.

Docker Engine includes:

- Docker Daemon
- Docker API
- Docker CLI

---

### Images and Containers are the same.

Incorrect.

Images are templates.

Containers are running instances of those templates.

---

# Best Practices

- Keep the Docker Daemon updated.
- Use trusted registries.
- Store images in version-controlled repositories.
- Separate application services into individual containers.
- Use volumes for persistent data.
- Secure access to the Docker API.
- Monitor Docker resources in production.

---

# Related Topics

- Introduction to Docker
- Why Docker
- Virtual Machines vs Containers
- Docker Engine
- Docker Images
- Docker Containers
- Docker Networking
- Docker Volumes

---

## Key Takeaways

- Docker uses a client-server architecture in which the Docker Client communicates with the Docker Daemon through the Docker API.
- The Docker Daemon is responsible for building images, running containers, managing networks, and handling persistent storage.
- Docker Images are immutable templates, while Docker Containers are running instances of those images.
- Docker Registries, Networks, and Volumes extend Docker's architecture by providing image distribution, container communication, and persistent storage.
- Understanding Docker architecture provides the foundation for learning image management, container lifecycle, networking, storage, orchestration, and production deployments.