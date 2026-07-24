# Docker & Kubernetes Issues

## Overview

Redis is widely deployed inside **Docker containers** and **Kubernetes clusters** because they provide portability, scalability, and simplified deployments.

However, containerized environments introduce additional operational challenges that do not exist on traditional virtual machines.

Common issues include:

- Redis container repeatedly restarting
- CrashLoopBackOff
- OOMKilled
- Data loss after restart
- Persistent Volume problems
- Network connectivity failures
- Service discovery failures
- Configuration issues
- CPU throttling
- Memory limits
- Slow startup

This chapter provides a structured approach for troubleshooting Redis in containerized production environments.

---

# Architecture Overview

## Docker

```
+----------------------+

|   Docker Host        |

|                      |

| +------------------+ |

| | Redis Container  | |

| +------------------+ |

|         │            |

|         ▼            |

| Docker Volume        |

+----------------------+
```

---

## Kubernetes

```
              Client

                 │

                 ▼

          Kubernetes Service

                 │

        ┌────────┴────────┐

        ▼                 ▼

 Redis Pod 1         Redis Pod 2

        │                 │

        ▼                 ▼

 Persistent Volume   Persistent Volume
```

---

# Common Problems

| Problem | Symptoms |
|----------|----------|
| CrashLoopBackOff | Pod continuously restarts |
| OOMKilled | Container terminated due to memory |
| Data loss | Missing persistence after restart |
| PVC Pending | Redis cannot start |
| Service unreachable | Connection refused |
| DNS failure | Hostname resolution fails |
| CPU throttling | High latency |
| Volume mount failure | Startup failure |
| Wrong ConfigMap | Invalid Redis configuration |

---

# Docker Troubleshooting

---

## Verify Container Status

```bash
docker ps
```

Expected

```
STATUS

Up
```

If container exited

```
Exited (1)
```

inspect logs.

---

## View Logs

```bash
docker logs redis
```

Common messages

```
Permission denied

Cannot allocate memory

Fatal error loading RDB
```

Logs are the first place to investigate.

---

## Inspect Container

```bash
docker inspect redis
```

Verify

- Network
- Volumes
- Environment variables
- Restart policy
- Memory limits

---

## Verify Volume Mount

```
Redis

↓

Docker Volume

↓

Host Storage
```

Example

```bash
docker volume ls
```

Inspect

```bash
docker volume inspect redis-data
```

Without persistent volumes

↓

Container restart

↓

Data loss

---

## Restart Policy

Recommended

```yaml
restart: unless-stopped
```

Avoid

```
restart: no
```

for production workloads.

---

# Docker Networking

Verify network

```bash
docker network ls
```

Inspect

```bash
docker network inspect bridge
```

Containers should communicate using

```
Service Names
```

instead of

```
Container IP
```

---

# Docker Resource Limits

Example

```yaml
deploy:

  resources:

    limits:

      memory: 2G

      cpus: "2"
```

Incorrect limits

↓

OOMKilled

↓

Performance degradation

---

# Kubernetes Troubleshooting

---

## Verify Pod Status

```bash
kubectl get pods
```

Healthy

```
Running
```

Problem states

```
CrashLoopBackOff

Pending

OOMKilled

ContainerCreating
```

---

## Describe Pod

```bash
kubectl describe pod redis-0
```

Useful information

- Events
- Scheduling
- Image pull errors
- Volume mount failures

---

## View Logs

```bash
kubectl logs redis-0
```

If restarting

```bash
kubectl logs redis-0 --previous
```

Always inspect previous logs after crashes.

---

# CrashLoopBackOff

Typical workflow

```
Pod Starts

↓

Redis Fails

↓

Restart

↓

CrashLoopBackOff
```

Common causes

- Invalid configuration
- Missing volume
- Memory exhaustion
- Startup script failure

---

# OOMKilled

Architecture

```
Redis

↓

Memory Limit

↓

Exceeded

↓

Kernel OOM Killer

↓

Restart
```

Verify

```bash
kubectl describe pod redis
```

Look for

```
OOMKilled
```

---

# Persistent Volume Problems

Verify

```bash
kubectl get pvc
```

Expected

```
Bound
```

Problem

```
Pending
```

↓

Redis cannot start.

---

# Storage Class

Check

```bash
kubectl get storageclass
```

Ensure PVC references a valid StorageClass.

---

# ConfigMap Issues

Verify

```bash
kubectl describe configmap redis-config
```

Incorrect configuration

↓

Redis startup failure.

---

# Secret Issues

Check

```bash
kubectl get secrets
```

Describe

```bash
kubectl describe secret redis-secret
```

Common issues

- Missing password
- Incorrect mount
- Wrong namespace

---

# Service Problems

Verify

```bash
kubectl get svc
```

Example

```
redis-service
```

Test

```bash
kubectl exec -it app -- redis-cli -h redis-service
```

---

# DNS Resolution

Inside Pod

```bash
nslookup redis-service
```

Expected

```
ClusterIP
```

Failure indicates Kubernetes DNS issues.

---

# Network Policies

Example

```
Application

↓

Network Policy

↓

Redis
```

Policies may block traffic.

Verify

```bash
kubectl get networkpolicy
```

---

# StatefulSet

Redis should generally use

```
StatefulSet
```

instead of

```
Deployment
```

Reasons

- Stable identity
- Stable hostname
- Persistent storage
- Ordered startup

---

# Liveness Probe

Example

```yaml
livenessProbe:

  tcpSocket:

    port: 6379
```

Incorrect probes

↓

Restart loop

---

# Readiness Probe

Example

```yaml
readinessProbe:

  exec:

    command:

      - redis-cli

      - ping
```

Expected

```
PONG
```

Applications should only connect after readiness succeeds.

---

# CPU Throttling

Monitor

```bash
kubectl top pod redis
```

High throttling

↓

Latency

↓

Slow commands

Increase CPU requests if necessary.

---

# Memory Monitoring

Check

```bash
kubectl top pod redis
```

Compare usage against configured limits.

---

# Rolling Updates

Workflow

```
New Pod

↓

Ready

↓

Old Pod Removed
```

Improper updates

↓

Downtime

Use rolling deployments with readiness probes.

---

# Useful Commands

Docker

```bash
docker ps
```

```bash
docker logs redis
```

```bash
docker stats
```

Kubernetes

```bash
kubectl get pods
```

```bash
kubectl describe pod redis
```

```bash
kubectl logs redis
```

```bash
kubectl top pod redis
```

```bash
kubectl get pvc
```

---

# Diagnostic Workflow

```
Redis Issue

        │

        ▼

Docker or Kubernetes?

        │

 ┌──────┴───────────┐

 │                  │

Docker         Kubernetes

 │                  │

Logs           Pod Status

 │                  │

 ▼                  ▼

Volumes        PVC

 │                  │

 ▼                  ▼

Network        Service

 │                  │

 ▼                  ▼

Memory         OOMKilled

 │                  │

 ▼                  ▼

CPU            Restart Loop

 │

 ▼

Resolve Issue
```

---

# Common Mistakes

## No Persistent Storage

Containers are ephemeral.

Without persistent volumes,

all Redis data is lost after restart.

---

## Using Deployments Instead of StatefulSets

Redis requires stable network identities.

Use StatefulSets for production.

---

## Incorrect Resource Limits

Very small CPU or memory limits lead to throttling or OOM kills.

---

## Ignoring Pod Events

Most Kubernetes deployment issues are visible in

```bash
kubectl describe pod
```

Always review Events.

---

## Missing Health Checks

Without readiness and liveness probes,

Kubernetes cannot manage Redis correctly.

---

# Best Practices

- Use **StatefulSets** for production Redis deployments.
- Configure **Persistent Volumes** for durable storage.
- Implement liveness and readiness probes.
- Use ConfigMaps for configuration and Secrets for credentials.
- Set appropriate CPU and memory requests/limits.
- Monitor container restarts, OOM kills, and PVC health.
- Use service names instead of IP addresses for connectivity.
- Keep Redis and application pods within the same cluster or low-latency network.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Storage | Use SSD-backed Persistent Volumes |
| Memory | Leave headroom to avoid OOM kills |
| CPU | Prevent throttling with proper requests/limits |
| Networking | Use ClusterIP Services for internal traffic |
| Health Checks | Configure readiness and liveness probes |
| Monitoring | Track pod restarts, resource usage, and PVC status |

---

# Production Considerations

For production deployments:

- Deploy Redis using StatefulSets with persistent storage.
- Configure PodDisruptionBudgets to minimize downtime during maintenance.
- Use anti-affinity rules to distribute replicas across nodes.
- Monitor restart counts, OOMKilled events, PVC utilization, and probe failures.
- Regularly test node failures and storage recovery procedures.
- Integrate Kubernetes events with centralized logging and alerting.
- Maintain Infrastructure-as-Code (Helm, Kustomize, Terraform, etc.) for repeatable deployments.

---

# Summary

Running Redis in Docker and Kubernetes introduces operational considerations beyond Redis itself. Most production issues stem from container lifecycle management, persistent storage, networking, resource limits, and orchestration configuration. By systematically checking logs, pod status, volumes, services, and resource usage, engineers can resolve container-specific Redis issues quickly while maintaining high availability and performance.

---

# Key Takeaways

- Always use persistent storage for Redis containers.
- Prefer **StatefulSets** over Deployments for Kubernetes.
- Configure liveness and readiness probes correctly.
- Monitor pod restarts, OOMKilled events, and PVC health.
- Use service names instead of IP addresses for networking.
- Allocate sufficient CPU and memory to avoid throttling.
- Review logs and Kubernetes Events as the first step in troubleshooting.
- Treat container orchestration as an integral part of Redis operations, not just the runtime environment.