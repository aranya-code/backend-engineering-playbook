# Docker Containers

## Overview

Docker containers are the runtime instances of Docker images. They provide isolated environments for applications while sharing the host operating system's kernel. Understanding containers is essential for backend developers, as interviewers frequently ask about the container lifecycle, isolation, storage, networking, resource management, and production best practices.

This section contains beginner to advanced Docker container interview questions with concise, interview-ready answers.

---

# Basic Interview Questions

## 1. What is a Docker container?

**Answer**

A Docker container is a lightweight, isolated runtime instance created from a Docker image.

It contains:

- Application code
- Runtime
- Libraries
- Dependencies
- Configuration

Containers share the host operating system's kernel while remaining isolated from each other.

---

## 2. How is a container created?

**Answer**

A container is created from a Docker image.

Example:

```bash
docker run nginx
```

Docker first checks whether the image exists locally. If not, it downloads the image and creates a new container.

---

## 3. What is the difference between creating and starting a container?

**Answer**

- **Create** allocates the container without starting it.
- **Start** runs an existing container.

Examples:

```bash
docker create nginx
```

```bash
docker start container_name
```

---

## 4. How do you list running containers?

**Answer**

```bash
docker ps
```

---

## 5. How do you list all containers?

**Answer**

```bash
docker ps -a
```

---

## 6. How do you stop a container?

**Answer**

```bash
docker stop container_name
```

Docker sends a graceful termination signal before stopping the container.

---

## 7. How do you forcefully stop a container?

**Answer**

```bash
docker kill container_name
```

This immediately terminates the container process.

---

## 8. How do you restart a container?

**Answer**

```bash
docker restart container_name
```

---

## 9. How do you remove a container?

**Answer**

```bash
docker rm container_name
```

To remove a running container:

```bash
docker rm -f container_name
```

---

## 10. Can multiple containers be created from one image?

**Answer**

Yes.

A single Docker image can create multiple independent containers.

Each container has:

- Its own writable layer
- Independent processes
- Separate network namespace

---

# Intermediate Interview Questions

## 11. What is the Docker container lifecycle?

**Answer**

A typical lifecycle is:

```text
Created
   │
   ▼
Running
   │
   ▼
Paused
   │
   ▼
Stopped
   │
   ▼
Removed
```

---

## 12. What happens when a container stops?

**Answer**

- Running processes terminate.
- Files in the writable layer remain.
- Volumes remain unchanged.
- The container can be restarted unless removed.

---

## 13. What happens when a container is removed?

**Answer**

Docker removes:

- Writable container layer
- Metadata
- Network configuration

Named volumes are **not** removed unless explicitly deleted.

---

## 14. What is the writable layer?

**Answer**

Containers receive a thin writable layer on top of the read-only image layers.

Any changes made during execution are stored in this writable layer.

---

## 15. What happens if a container is deleted without using volumes?

**Answer**

All data stored inside the writable layer is permanently lost.

Persistent data should always be stored in Docker volumes or external storage.

---

## 16. What is the difference between `docker run`, `docker create`, and `docker start`?

**Answer**

| Command | Purpose |
|----------|----------|
| `docker create` | Creates a container only |
| `docker start` | Starts an existing container |
| `docker run` | Creates and starts a container |

---

## 17. What is the difference between `docker stop` and `docker kill`?

**Answer**

| docker stop | docker kill |
|--------------|-------------|
| Graceful shutdown | Immediate termination |
| Sends SIGTERM then SIGKILL | Sends SIGKILL immediately |
| Allows cleanup | No cleanup |

---

## 18. How do you execute commands inside a running container?

**Answer**

```bash
docker exec -it container_name sh
```

or

```bash
docker exec -it container_name bash
```

---

## 19. How do you inspect a running container?

**Answer**

```bash
docker inspect container_name
```

---

## 20. How do you view container logs?

**Answer**

```bash
docker logs container_name
```

Follow logs:

```bash
docker logs -f container_name
```

---

# Advanced Interview Questions

## 21. What is the difference between `docker exec` and `docker attach`?

**Answer**

| docker exec | docker attach |
|--------------|---------------|
| Starts a new process | Connects to the main process |
| Safe for production | May interrupt the application |
| Most commonly used | Less frequently used |

---

## 22. Can a stopped container be restarted?

**Answer**

Yes.

As long as it has not been removed.

```bash
docker start container_name
```

---

## 23. Why are containers considered isolated?

**Answer**

Docker uses Linux namespaces to isolate:

- Processes
- Network
- Filesystem
- Hostname
- Users

This prevents containers from interfering with each other.

---

## 24. How does Docker limit container resources?

**Answer**

Docker uses Linux cgroups.

Examples:

```bash
docker run --memory=1g
```

```bash
docker run --cpus=2
```

---

## 25. Why shouldn't production containers run as root?

**Answer**

Running as root increases security risks.

Best practice:

```dockerfile
USER appuser
```

This limits potential damage if the container is compromised.

---

# Scenario-Based Interview Questions

## 26. Your container exits immediately after starting. What would you check?

**Expected Answer**

- Container logs
- Startup command
- Dockerfile CMD/ENTRYPOINT
- Environment variables
- Application errors
- Missing dependencies

Useful commands:

```bash
docker logs container_name
```

```bash
docker inspect container_name
```

---

## 27. A container keeps restarting. How would you troubleshoot it?

**Expected Answer**

- Review restart policy
- Inspect logs
- Check health checks
- Verify configuration
- Ensure dependent services are available
- Review resource usage

---

## 28. Your application data disappears after removing a container. Why?

**Expected Answer**

The application stored data inside the container's writable layer instead of using a Docker volume.

Persistent data should always be stored in named volumes or external storage.

---

## 29. A container cannot communicate with another container. What would you investigate?

**Expected Answer**

- Docker network configuration
- Service names
- Container status
- Firewall rules
- Published ports
- DNS resolution

---

## 30. How would you debug a production container?

**Expected Answer**

Typical workflow:

1. Check container status.
2. Review logs.
3. Inspect configuration.
4. Monitor CPU and memory.
5. Verify networking.
6. Check mounted volumes.
7. Investigate recent deployments.

Useful commands:

```bash
docker ps
docker logs
docker inspect
docker stats
docker exec
```

---

# Production-Level Questions

## 31. Should containers store application data?

**Answer**

No.

Containers should be treated as ephemeral.

Persistent data should be stored in:

- Docker volumes
- Databases
- Object storage
- Network storage

---

## 32. How should production containers be monitored?

**Answer**

Typical monitoring includes:

- CPU usage
- Memory usage
- Disk usage
- Restart count
- Health checks
- Logs
- Application metrics

Common tools:

- Prometheus
- Grafana
- Loki
- ELK Stack

---

## 33. What are restart policies?

**Answer**

Restart policies determine how Docker handles container failures.

Examples:

- `no`
- `on-failure`
- `always`
- `unless-stopped`

---

# Interview Tips

- Know the complete container lifecycle.
- Understand the difference between images and containers.
- Be comfortable with `docker exec`, `docker logs`, `docker inspect`, and `docker stats`.
- Explain why containers are ephemeral.
- Expect troubleshooting and production-focused questions rather than just CLI commands.

---

## Key Takeaways

- Containers are lightweight runtime instances created from Docker images.
- Docker provides commands to create, start, stop, inspect, and manage containers throughout their lifecycle.
- Containers are isolated using Linux namespaces and managed using cgroups for resource control.
- Persistent application data should always be stored outside the container's writable layer.
- Strong knowledge of container lifecycle, debugging, resource management, and production best practices is essential for Docker interviews.