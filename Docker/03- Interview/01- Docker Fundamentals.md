# Docker Fundamentals

## Overview

Docker Fundamentals is one of the most important interview topics for backend developers, DevOps engineers, and platform engineers. Interviewers use these questions to evaluate your understanding of containers, virtualization, Docker architecture, and why Docker has become the industry standard for packaging and deploying applications.

This section contains beginner to advanced Docker fundamentals interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. What is Docker?

**Answer**

Docker is an open-source containerization platform that enables developers to package applications and their dependencies into lightweight, portable containers. These containers run consistently across development, testing, and production environments.

---

## 2. Why is Docker used?

**Answer**

Docker provides several benefits:

- Consistent development and production environments
- Faster application deployment
- Lightweight compared to virtual machines
- Efficient resource utilization
- Easy application distribution
- Simplified dependency management
- Improved CI/CD workflows
- Better scalability

---

## 3. What is containerization?

**Answer**

Containerization is the process of packaging an application along with its runtime, libraries, dependencies, and configuration into a container that can run consistently on any system supporting Docker.

---

## 4. What problem does Docker solve?

**Answer**

Docker eliminates the classic problem of:

> "It works on my machine."

By packaging applications with all required dependencies, Docker ensures consistent behavior across different environments.

---

## 5. What is a Docker container?

**Answer**

A Docker container is a lightweight, isolated runtime instance created from a Docker image.

It includes:

- Application
- Runtime
- Libraries
- Dependencies
- Configuration

Containers share the host operating system's kernel while remaining isolated from one another.

---

## 6. What is a Docker image?

**Answer**

A Docker image is a read-only, immutable template used to create containers.

It contains:

- Application code
- Runtime
- System libraries
- Dependencies
- Startup commands

---

## 7. What is the difference between an image and a container?

**Answer**

| Docker Image | Docker Container |
|--------------|------------------|
| Read-only template | Running instance of an image |
| Immutable | Mutable during execution |
| Stored in a registry or locally | Runs application processes |
| Used to create containers | Created from images |

---

## 8. What is Docker Engine?

**Answer**

Docker Engine is the core runtime responsible for building, running, and managing Docker containers.

It includes:

- Docker Daemon (`dockerd`)
- Docker CLI
- Docker REST API

---

## 9. What is Docker Desktop?

**Answer**

Docker Desktop is a desktop application for Windows and macOS that bundles:

- Docker Engine
- Docker CLI
- Docker Compose
- Docker Dashboard
- Kubernetes (optional)
- WSL 2 integration (Windows)

---

## 10. What is Docker Hub?

**Answer**

Docker Hub is Docker's public container registry where developers can:

- Store Docker images
- Share images
- Download official images
- Publish private repositories

---

# Intermediate Interview Questions

## 11. How does Docker work?

**Answer**

Docker follows a client-server architecture.

Components include:

- Docker CLI
- Docker Daemon
- Docker Images
- Docker Containers
- Docker Registries

The CLI sends commands to the Docker Daemon, which builds images, starts containers, and manages Docker resources.

---

## 12. What is Docker's client-server architecture?

**Answer**

Docker consists of:

```
Docker CLI
       │
       ▼
Docker Daemon
       │
       ▼
Containers / Images / Networks / Volumes
```

The Docker CLI communicates with the Docker Daemon using the Docker API.

---

## 13. What is the Docker Daemon?

**Answer**

The Docker Daemon (`dockerd`) is the background service responsible for:

- Building images
- Running containers
- Managing networks
- Managing volumes
- Pulling images
- Pushing images

---

## 14. What is Docker CLI?

**Answer**

Docker CLI is the command-line interface used to interact with Docker.

Examples:

```bash
docker run
docker build
docker ps
docker images
docker logs
```

---

## 15. What is a Docker Registry?

**Answer**

A Docker Registry stores Docker images.

Examples include:

- Docker Hub
- Amazon ECR
- Azure Container Registry
- Google Artifact Registry
- GitHub Container Registry
- Harbor

---

## 16. What is the difference between Docker and Virtual Machines?

**Answer**

| Docker | Virtual Machine |
|---------|-----------------|
| Shares host OS kernel | Runs a complete guest OS |
| Lightweight | Heavyweight |
| Fast startup | Slower startup |
| Lower resource usage | Higher resource usage |
| Better density | Lower density |

---

## 17. Can Docker run without virtualization?

**Answer**

On Linux, Docker uses kernel features such as namespaces and cgroups, so traditional hardware virtualization is not required.

On Windows and macOS, Docker Desktop relies on virtualization technologies (WSL 2, Hyper-V, or a lightweight VM) because Docker containers require a Linux kernel.

---

## 18. What are namespaces?

**Answer**

Namespaces isolate system resources for containers.

Examples include:

- Process IDs
- Network interfaces
- Mount points
- Hostnames
- Users

They ensure containers remain isolated from one another.

---

## 19. What are cgroups?

**Answer**

Control Groups (cgroups) limit and monitor resource usage such as:

- CPU
- Memory
- Disk I/O
- Network bandwidth

They help prevent one container from monopolizing system resources.

---

## 20. What resources does Docker manage?

**Answer**

Docker manages:

- Images
- Containers
- Networks
- Volumes
- Build cache
- Secrets (Swarm)
- Configs (Swarm)

---

# Advanced Interview Questions

## 21. Why is Docker considered lightweight?

**Answer**

Containers share the host operating system's kernel instead of running separate guest operating systems, resulting in:

- Lower memory usage
- Faster startup
- Smaller footprint
- Better resource utilization

---

## 22. Is Docker a virtualization technology?

**Answer**

No.

Docker is a **containerization** platform, not a traditional virtualization platform.

It uses operating system-level isolation rather than hardware virtualization.

---

## 23. Can multiple containers use the same image?

**Answer**

Yes.

Multiple containers can be created from the same image. Each container has its own writable layer while sharing the underlying read-only image layers.

---

## 24. Why are Docker containers portable?

**Answer**

Containers package the application together with its dependencies, making them independent of the underlying environment as long as Docker is available.

---

## 25. What is the Docker lifecycle?

**Answer**

Typical lifecycle:

```
Dockerfile
      │
      ▼
Image
      │
      ▼
Container Created
      │
      ▼
Running
      │
      ▼
Stopped
      │
      ▼
Removed
```

---

# Scenario-Based Interview Questions

## 26. A developer says, "The application works on my machine but not on production." How can Docker help?

**Expected Answer**

Docker packages the application with all required dependencies and configuration, ensuring consistent execution across development, testing, and production environments.

---

## 27. Why would a company choose Docker instead of virtual machines?

**Expected Answer**

- Faster deployments
- Lower infrastructure costs
- Better scalability
- Higher resource utilization
- Easier CI/CD integration
- Consistent environments

---

## 28. When would Docker not be the right solution?

**Expected Answer**

Docker may not be ideal when:

- Applications require different operating system kernels.
- Full hardware virtualization is needed.
- Strong VM-level isolation is mandatory.
- Legacy software depends on a complete operating system environment.

---

# Interview Tips

- Clearly distinguish **containers** from **virtual machines**.
- Be prepared to explain Docker's client-server architecture.
- Understand how namespaces and cgroups enable container isolation.
- Explain why Docker provides portability and consistency.
- Avoid saying Docker "replaces" virtual machines—each serves different use cases.

---

## Key Takeaways

- Docker is a containerization platform that packages applications and their dependencies into portable containers.
- Containers are lightweight because they share the host operating system's kernel.
- Docker Engine consists of the Docker CLI, Docker Daemon, and Docker API.
- Namespaces provide isolation, while cgroups manage resource allocation.
- A strong understanding of Docker fundamentals forms the foundation for more advanced topics such as Dockerfiles, networking, volumes, Compose, and Swarm.