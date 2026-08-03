# Performance and Resource Issues

## Overview

Docker containers share the host operating system's kernel and system resources. While containers are lightweight compared to virtual machines, poor resource management can lead to slow applications, container crashes, high CPU utilization, excessive memory consumption, disk exhaustion, and degraded system performance.

This guide covers the most common Docker performance and resource-related issues, explains how to diagnose them, and provides practical solutions and preventive best practices.

---

## Common Performance and Resource Issues

| Issue | Severity |
|--------|----------|
| High CPU usage | High |
| High memory usage | High |
| Container killed with Exit Code 137 (OOMKilled) | High |
| Disk space exhausted | High |
| High disk I/O | Medium |
| Slow image builds | Medium |
| Slow container startup | Medium |
| Large Docker images | Medium |
| Excessive log file growth | Medium |
| Too many unused Docker resources | Low |

---

# Issue 1: High CPU Usage

## Symptoms

- Containers consume excessive CPU.
- Host machine becomes sluggish.
- Application response times increase.

---

## Possible Causes

- Infinite loops.
- Inefficient application code.
- Too many running containers.
- Background processes.

---

## How to Diagnose

Monitor resource usage:

```bash
docker stats
```

View container processes:

```bash
docker top <container_name>
```

Monitor system processes:

```bash
top
```

---

## Solutions

Restart the container if necessary.

Optimize application logic.

Limit CPU usage:

```bash
docker run --cpus="2" image_name
```

---

## Prevention

- Profile applications regularly.
- Configure CPU limits.
- Remove unnecessary background processes.

---

# Issue 2: High Memory Usage

## Symptoms

- Container consumes excessive RAM.
- Host begins swapping memory.
- Slow application performance.

---

## Possible Causes

- Memory leaks.
- Large caches.
- Inefficient application logic.
- Too many running services.

---

## How to Diagnose

Monitor memory:

```bash
docker stats
```

Inspect container:

```bash
docker inspect <container_name>
```

View host memory:

```bash
free -h
```

---

## Solutions

Restart the container.

Fix memory leaks.

Limit memory usage:

```bash
docker run --memory=1g image_name
```

---

## Prevention

- Monitor memory consumption.
- Profile applications.
- Set memory limits in production.

---

# Issue 3: Exit Code 137 (OOMKilled)

## Symptoms

Container exits with:

```text
Exited (137)
```

---

## Possible Causes

- Out of memory.
- Kernel terminated the container.
- Memory limit exceeded.

---

## How to Diagnose

Inspect the container:

```bash
docker inspect <container_name>
```

Monitor usage:

```bash
docker stats
```

---

## Solutions

Increase available memory.

Optimize memory usage.

Configure appropriate memory limits.

---

## Prevention

Always monitor memory-intensive workloads.

---

# Issue 4: Disk Space Exhausted

## Symptoms

```text
no space left on device
```

---

## Possible Causes

- Old images.
- Unused containers.
- Dangling volumes.
- Build cache.

---

## How to Diagnose

View Docker disk usage:

```bash
docker system df
```

Check filesystem usage:

```bash
df -h
```

---

## Solutions

Remove unused resources:

```bash
docker system prune
```

Remove unused images:

```bash
docker image prune
```

Remove unused volumes:

```bash
docker volume prune
```

---

## Prevention

Perform regular Docker cleanup.

Monitor disk usage.

---

# Issue 5: High Disk I/O

## Symptoms

- Slow container performance.
- Delayed database operations.
- Increased disk utilization.

---

## Possible Causes

- Heavy logging.
- Large database writes.
- Frequent file synchronization.
- Slow storage devices.

---

## How to Diagnose

Monitor disk activity:

Linux

```bash
iostat
```

Check Docker statistics:

```bash
docker stats
```

---

## Solutions

Reduce unnecessary writes.

Move data to faster storage.

Optimize database operations.

---

## Prevention

Use SSD storage for production workloads.

Rotate log files.

---

# Issue 6: Slow Image Builds

## Symptoms

Docker builds take significantly longer than expected.

---

## Possible Causes

- Poor Dockerfile ordering.
- Large build context.
- No build cache.
- Large dependencies.

---

## How to Diagnose

Build with verbose output:

```bash
docker build --progress=plain .
```

---

## Solutions

Optimize Dockerfile layer ordering.

Use `.dockerignore`.

Leverage build cache effectively.

---

## Prevention

Use multi-stage builds.

Minimize the build context.

---

# Issue 7: Slow Container Startup

## Symptoms

Containers require a long time to become operational.

---

## Possible Causes

- Large images.
- Slow initialization scripts.
- Waiting for dependencies.
- Database migrations during startup.

---

## How to Diagnose

Review startup logs:

```bash
docker logs <container_name>
```

Measure startup time.

---

## Solutions

Reduce image size.

Optimize startup scripts.

Move lengthy initialization tasks outside the startup process where possible.

---

## Prevention

Keep images lean.

Use health checks.

---

# Issue 8: Large Docker Images

## Symptoms

Images require significant time to build, pull, and deploy.

---

## Possible Causes

- Unnecessary packages.
- Large dependencies.
- Multiple unused layers.

---

## How to Diagnose

Inspect image history:

```bash
docker history <image_name>
```

View image sizes:

```bash
docker images
```

---

## Solutions

Use lightweight base images.

Adopt multi-stage builds.

Remove temporary files during image creation.

---

## Prevention

Regularly review image contents.

Keep dependencies minimal.

---

# Issue 9: Excessive Log File Growth

## Symptoms

Docker log files consume significant disk space.

---

## Possible Causes

- Verbose application logging.
- Missing log rotation.
- Long-running containers.

---

## How to Diagnose

Inspect log size:

```bash
du -sh /var/lib/docker/containers
```

---

## Solutions

Configure log rotation.

Example (`daemon.json`):

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker after applying changes.

---

## Prevention

Enable log rotation in all production environments.

---

# Issue 10: Excessive Unused Docker Resources

## Symptoms

Docker consumes increasing amounts of disk space over time.

---

## Possible Causes

- Dangling images.
- Unused networks.
- Unused containers.
- Build cache.

---

## How to Diagnose

View resource usage:

```bash
docker system df
```

List unused resources.

---

## Solutions

Remove unused resources:

```bash
docker system prune
```

Remove unused build cache:

```bash
docker builder prune
```

---

## Prevention

Schedule periodic cleanup tasks.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| Monitor resource usage | `docker stats` |
| View running processes | `docker top <container>` |
| Inspect container | `docker inspect <container>` |
| View disk usage | `docker system df` |
| Remove unused resources | `docker system prune` |
| Remove build cache | `docker builder prune` |
| View image history | `docker history <image>` |
| View image sizes | `docker images` |
| View logs | `docker logs <container>` |
| Check filesystem usage | `df -h` |

---

# Best Practices

- Configure CPU and memory limits for production containers.
- Use multi-stage builds to reduce image size.
- Monitor resource utilization continuously.
- Enable log rotation.
- Remove unused Docker resources regularly.
- Keep Docker images small and optimized.
- Profile applications before deploying to production.
- Use monitoring tools such as Prometheus and Grafana for long-term resource tracking.

---

# Related Topics

- Docker Images
- Docker Containers
- Docker Volumes
- Docker Compose
- Docker Swarm
- Docker Monitoring
- Docker CLI

---

## Key Takeaways

- Performance issues are often caused by excessive CPU usage, memory leaks, large images, or insufficient resource management.
- `docker stats`, `docker system df`, and `docker inspect` are essential tools for diagnosing resource-related problems.
- Setting appropriate CPU and memory limits improves application stability.
- Optimizing Dockerfiles, enabling log rotation, and performing regular cleanup significantly improve Docker performance.
- Continuous monitoring and proactive resource management are key to maintaining healthy Docker environments.