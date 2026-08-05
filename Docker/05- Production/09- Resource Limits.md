# Resource Limits

## Overview

Containers share the host machine's CPU, memory, storage, and other system resources. By default, Docker allows containers to consume as many resources as they can, which means one poorly behaving application can impact every other container running on the same host.

Resource limits allow you to control how much CPU, memory, and other resources a container can use. Properly configured limits improve system stability, prevent resource starvation, and create more predictable production environments.

---

# Why Resource Limits Matter

Without limits:

```text
Container A

↓

Consumes All Memory

↓

Other Containers Slow Down

↓

System Becomes Unstable
```

With limits:

```text
Container A

↓

Memory Limit Reached

↓

Container Restricted

↓

Other Containers Continue Running
```

---

# Types of Resource Limits

Docker allows you to limit several resources.

| Resource | Purpose |
|----------|----------|
| Memory | Prevent excessive RAM usage |
| CPU | Limit processor utilization |
| PIDs | Limit number of processes |
| Swap | Control swap memory |
| Storage | Limit writable layer size (storage-driver dependent) |
| File Descriptors | Operating system limit |

---

# Resource Management Workflow

```text
Application

↓

Container

↓

Resource Limits

↓

Host Resources
```

---

# Memory Limits

Memory limits prevent containers from consuming all available RAM.

Example

```yaml
services:

  app:

    mem_limit: 512m
```

Workflow

```text
Application

↓

Uses Memory

↓

512 MB Limit

↓

Cannot Exceed Limit
```

---

# Why Memory Limits Are Important

Without limits:

```text
Container

↓

Memory Leak

↓

Host RAM Exhausted

↓

Multiple Services Fail
```

With limits:

```text
Container

↓

Memory Leak

↓

Limit Reached

↓

Container Stopped

↓

Other Services Protected
```

---

# CPU Limits

Limit CPU usage.

Example

```yaml
cpus: 1.0
```

This allows the container to use approximately one CPU core.

Examples

```yaml
cpus: 0.5
```

Half a CPU.

```yaml
cpus: 2
```

Two CPU cores.

---

# CPU Scheduling

```text
Host CPU

│

├── Container A

├── Container B

└── Container C
```

CPU limits help Docker distribute processing fairly between containers.

---

# PID Limits

Containers can accidentally create excessive processes.

Example

```yaml
pids_limit: 200
```

Workflow

```text
Application

↓

Creates Processes

↓

200 Process Limit

↓

Further Processes Blocked
```

PID limits help protect against runaway process creation.

---

# Swap Memory

Docker also allows swap configuration.

Example

```bash
docker run \
    --memory=512m \
    --memory-swap=1g
```

Meaning

```text
RAM

↓

512 MB

+

Swap

↓

512 MB

=

1 GB Total
```

Swap usage should generally be minimized for latency-sensitive applications.

---

# Resource Limits Example

```yaml
services:

  api:

    image: myapp:1.0.0

    mem_limit: 512m

    cpus: 1.0

    pids_limit: 200
```

This creates a predictable runtime environment.

---

# Resource Allocation

```text
Host

│

├── API

│      512 MB

│      1 CPU

│

├── Redis

│      256 MB

│      0.5 CPU

│

└── PostgreSQL

       1 GB

       2 CPUs
```

Each container receives an appropriate share of host resources.

---

# Monitoring Resource Usage

View live statistics.

```bash
docker stats
```

Example output

```text
CONTAINER      CPU %      MEM USAGE

api            12%        180 MB

redis          2%         48 MB

postgres       15%        420 MB
```

---

# Inspect Resource Configuration

```bash
docker inspect container_name
```

Useful information includes:

- Memory limits
- CPU limits
- Restart policy
- Health status

---

# Resource Exhaustion

Example

```text
Application

↓

Memory Leak

↓

512 MB Limit

↓

OOM Kill

↓

Restart Policy

↓

Container Restarted
```

Resource limits often work together with restart policies.

---

# Choosing Memory Limits

General recommendations

| Application | Example Memory |
|-------------|---------------:|
| Nginx | 128–256 MB |
| Redis | 256–1024 MB |
| FastAPI | 256–1024 MB |
| Django | 512 MB–2 GB |
| PostgreSQL | Depends on workload |

These values are starting points only and should be adjusted based on monitoring and testing.

---

# Choosing CPU Limits

Example

| Service | Example CPUs |
|----------|-------------:|
| API | 1 |
| Redis | 0.5 |
| PostgreSQL | 2 |
| Celery Worker | 1 |

Real production workloads should be benchmarked before finalizing limits.

---

# Resource Planning

```text
Host

↓

Available Resources

↓

Allocate Resources

↓

Deploy Containers

↓

Monitor Usage

↓

Adjust Limits
```

Resource planning is an ongoing process rather than a one-time configuration.

---

# Common Mistakes

## No Memory Limits

Containers may consume all available RAM.

---

## Excessively Low Limits

Example

```yaml
mem_limit: 32m
```

The application may fail to start or become unstable.

---

## Ignoring Monitoring

Resource limits should be based on actual usage rather than guesswork.

---

## Unlimited CPU

CPU-intensive applications can affect the performance of other services if left unrestricted.

---

## Setting the Same Limits Everywhere

Different applications have different resource requirements.

Database servers typically require more memory than reverse proxies.

---

# Resource Limits vs Reservations

Some container platforms distinguish between:

| Reservation | Limit |
|-------------|-------|
| Guaranteed minimum | Maximum allowed |

Docker Compose primarily focuses on limits, while orchestration platforms such as Kubernetes also support resource requests and limits.

---

# Production Checklist

Before deployment:

- Memory limit configured
- CPU limit configured
- PID limit configured
- Resource usage monitored
- Limits tested under load
- Restart policies configured
- Health checks enabled
- Capacity planning completed

---

# Best Practices

- Configure memory limits for every production container.
- Set CPU limits based on expected workload.
- Monitor resource usage continuously.
- Adjust limits using real production metrics.
- Avoid overcommitting host resources.
- Combine resource limits with health checks and restart policies.
- Test applications under realistic load before production deployment.
- Review resource allocation periodically as workloads evolve.

---

# Key Takeaways

- Resource limits protect the host system from runaway containers and improve overall stability.
- Memory, CPU, and PID limits should be configured for every long-running production service.
- Resource planning should be driven by monitoring and performance testing rather than assumptions.
- Proper limits help isolate failures, improve predictability, and ensure fair resource sharing across containers.
- Resource limits, health checks, monitoring, and restart policies work together to create resilient production Docker deployments.