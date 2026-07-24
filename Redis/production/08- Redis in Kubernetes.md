# Redis in Kubernetes

## Overview

Kubernetes has become the de facto platform for deploying modern cloud-native applications. Running Redis on Kubernetes provides benefits such as automated deployments, self-healing, rolling updates, and simplified scaling. However, Redis is a **stateful application**, which introduces additional operational challenges compared to stateless services.

This chapter explores production-ready Redis deployments on Kubernetes, including architecture, StatefulSets, persistent storage, high availability, monitoring, security, and operational best practices.

---

# Why Run Redis on Kubernetes?

Benefits include:

- Automated deployment
- Self-healing
- Rolling updates
- Infrastructure portability
- Horizontal application scaling
- Infrastructure as Code
- Easy monitoring integration
- Automated scheduling

Typical architecture

```
              Users

                │

                ▼

        Kubernetes Service

                │

        ┌───────┴────────┐

        ▼                ▼

    Django API      FastAPI API

             │

             ▼

      Redis Service

             │

             ▼

      Redis StatefulSet

             │

             ▼

     Persistent Volumes
```

---

# Why Redis is Stateful

Unlike application containers,

Redis stores data.

```
Application

↓

Stateless
```

```
Redis

↓

Stateful
```

If a Redis Pod disappears,

its data should not.

---

# Kubernetes Components

A production Redis deployment commonly uses:

- Namespace
- ConfigMap
- Secret
- StatefulSet
- Service
- PersistentVolume (PV)
- PersistentVolumeClaim (PVC)
- PodDisruptionBudget
- NetworkPolicy

---

# Architecture

```
                Kubernetes Cluster

                      │

      ┌───────────────┴────────────────┐

      ▼                                ▼

Redis Pod 0                      Redis Pod 1

      │                                │

      ▼                                ▼

 Persistent Volume             Persistent Volume
```

Each Redis Pod has dedicated storage.

---

# Why StatefulSet?

Redis should **not** normally use a Deployment.

Deployment

```
Pods

↓

Ephemeral
```

StatefulSet

```
Stable Identity

Stable Storage

Stable Network
```

StatefulSets preserve Pod identity across restarts.

---

# StatefulSet Characteristics

Each Pod receives

```
redis-0

redis-1

redis-2
```

instead of random names.

Stable naming simplifies replication.

---

# Persistent Volumes

Without storage

```
Pod Restart

↓

Data Lost
```

With Persistent Volumes

```
Redis Pod

↓

Persistent Volume

↓

Restart

↓

Data Preserved
```

---

# Persistent Volume Claim

```
Redis Pod

↓

PVC

↓

Persistent Volume

↓

Cloud Disk
```

The PVC abstracts storage provisioning.

---

# Storage Classes

Cloud providers expose storage through StorageClasses.

Examples

- AWS EBS
- Azure Managed Disk
- Google Persistent Disk
- Ceph
- Longhorn

StorageClasses automate volume creation.

---

# Redis Service

Applications connect using a Kubernetes Service.

```
Application

↓

Redis Service

↓

Redis Pods
```

Applications never connect directly to Pods.

---

# Headless Service

Redis replication requires direct Pod communication.

Headless Service

```
redis-0

redis-1

redis-2
```

Each Pod has its own DNS record.

---

# ConfigMap

Redis configuration should not be embedded inside container images.

Example

```
ConfigMap

↓

redis.conf

↓

Mounted into Pod
```

Configuration changes become easier.

---

# Secrets

Passwords should be stored securely.

Bad

```
redis.conf

↓

Password
```

Better

```
Kubernetes Secret

↓

Redis Pod
```

---

# Redis Authentication

Example

```conf
requirepass StrongPassword
```

Applications retrieve credentials from Kubernetes Secrets.

---

# Redis Persistence

Recommended production configuration

```
Redis

↓

RDB

+

AOF

↓

Persistent Volume
```

This provides durability and faster recovery.

---

# High Availability

Production architecture

```
           Redis Primary

                 │

        ┌────────┴────────┐

        ▼                 ▼

   Replica 1         Replica 2

        │

        ▼

     Sentinel
```

Multiple Sentinels detect failures.

---

# Redis Cluster

Large deployments often use Redis Cluster.

```
        Cluster

  ┌──────┼──────┐

  ▼      ▼      ▼

Node1 Node2 Node3

  │      │      │

Replica Replica Replica
```

Provides:

- Sharding
- Replication
- Automatic failover

---

# Pod Scheduling

Avoid placing every Redis Pod on one node.

Instead

```
Node A

↓

Redis-0
```

```
Node B

↓

Redis-1
```

```
Node C

↓

Redis-2
```

Node failures affect only one Redis Pod.

---

# Pod Anti-Affinity

Configure Pod Anti-Affinity

```
Redis-0

↓

Node A
```

```
Redis-1

↓

Node B
```

instead of

```
Node A

↓

Redis-0

Redis-1

Redis-2
```

---

# Pod Disruption Budget

Protects against maintenance downtime.

```
Upgrade

↓

One Pod Restarted

↓

Cluster Remains Available
```

---

# Resource Requests

Always define

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "500m"
```

This ensures proper scheduling.

---

# Resource Limits

Prevent resource exhaustion.

```yaml
limits:
  memory: "4Gi"
  cpu: "2"
```

---

# Liveness Probe

Detects unhealthy Redis Pods.

```
Pod

↓

PING

↓

Healthy?

↓

Restart if Needed
```

---

# Readiness Probe

Applications should not send traffic until Redis is ready.

```
Pod Starts

↓

Redis Loading

↓

Ready?

↓

Accept Traffic
```

---

# Rolling Updates

StatefulSets support controlled updates.

```
redis-2

↓

Updated

↓

Healthy

↓

redis-1

↓

Updated
```

Pods restart one at a time.

---

# Backup Strategy

Production backup workflow

```
Redis

↓

Snapshot

↓

Persistent Volume

↓

Object Storage

↓

Disaster Recovery
```

---

# Monitoring

Integrate

```
Redis

↓

redis_exporter

↓

Prometheus

↓

Grafana
```

Monitor

- Memory
- CPU
- Replication
- Latency
- Connected clients
- Evictions

---

# Logging

Logs should be centralized.

```
Redis

↓

Fluent Bit

↓

Elasticsearch

↓

Kibana
```

or

```
Redis

↓

OpenTelemetry

↓

Observability Platform
```

---

# Autoscaling

Redis itself is **not** horizontally autoscaled like stateless services.

Instead

Scale

```
Applications
```

independently.

Scale Redis using

- Cluster expansion
- Additional replicas
- Vertical scaling

---

# Security

Best practices

- Private namespaces
- Kubernetes Secrets
- TLS
- Network Policies
- RBAC
- ACLs

Never expose Redis publicly.

---

# Network Policy

Restrict access.

```
Application Namespace

↓

Redis Namespace

↓

Allowed
```

```
Other Pods

↓

Denied
```

---

# Helm

Most organizations deploy Redis using Helm.

Benefits

- Versioned deployments
- Easy upgrades
- Configuration management
- Repeatable installations

Popular charts

- Bitnami Redis
- Redis Community Helm Chart

---

# Operator-Based Deployment

Redis Operators automate operations.

Responsibilities

- Failover
- Scaling
- Upgrades
- Monitoring
- Backup

Examples

- Redis Operator
- Spotahome Redis Operator

---

# Production Architecture

```
                   Ingress

                      │

              Django / FastAPI

                      │

              Kubernetes Service

                      │

              Redis StatefulSet

          ┌───────────┼───────────┐

          ▼           ▼           ▼

      Redis-0     Redis-1     Redis-2

          │           │           │

          ▼           ▼           ▼

        PVC         PVC         PVC

          │

          ▼

   Cloud Persistent Storage

          │

          ▼

 Prometheus + Grafana
```

---

# Common Mistakes

## Using Deployment Instead of StatefulSet

Pods lose stable identity.

Replication becomes unreliable.

---

## No Persistent Storage

Pod restart

↓

Data loss.

---

## No Resource Limits

Redis may consume excessive memory and affect other workloads.

---

## All Pods on One Node

Single node failure

↓

Entire Redis cluster unavailable.

---

## Exposing Redis Publicly

Redis should always remain inside the cluster or private network.

---

## Ignoring Backup Strategy

Persistent volumes are **not** backups.

Use external backups.

---

# Best Practices

- Deploy Redis using StatefulSets.
- Use PersistentVolumes for every Redis Pod.
- Configure Pod Anti-Affinity across worker nodes.
- Enable RDB and AOF persistence.
- Deploy Redis Cluster or Sentinel for production HA.
- Monitor Redis with Prometheus and Grafana.
- Secure Redis using Secrets, Network Policies, TLS, and ACLs.
- Automate deployments using Helm or Operators.
- Test failover and recovery procedures regularly.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Storage | Use SSD-backed Persistent Volumes |
| Scheduling | Spread Pods across nodes |
| Networking | Use low-latency cluster networking |
| Resources | Define CPU and memory requests/limits |
| Monitoring | Track latency, memory, and replication |
| Updates | Perform rolling updates |

---

# Production Considerations

For production Kubernetes deployments:

- Use dedicated node pools for stateful workloads when possible.
- Configure PodDisruptionBudgets to minimize downtime during maintenance.
- Separate Redis from application Pods using namespaces and Network Policies.
- Regularly test StatefulSet upgrades, failover, and backup restoration.
- Monitor PersistentVolume capacity and I/O performance.
- Prefer Helm charts or Operators to standardize deployment and operational workflows.
- Integrate Redis into the organization's centralized logging and observability platform.

---

# Summary

Running Redis on Kubernetes provides automation, portability, and operational consistency, but it also requires careful management of state, storage, networking, and high availability. StatefulSets, PersistentVolumes, anti-affinity rules, monitoring, backups, and secure networking form the foundation of a production-ready Redis deployment on Kubernetes. By combining Kubernetes best practices with Redis operational guidance, organizations can build resilient, scalable, and maintainable cloud-native Redis infrastructure.

---

# Key Takeaways

- Redis is a stateful workload and should be deployed using StatefulSets.
- PersistentVolumes are essential for preserving data across Pod restarts.
- Use Headless Services for replication and stable Pod identities.
- Configure anti-affinity, resource limits, and health probes for resilient deployments.
- Secure Redis with Secrets, Network Policies, TLS, and ACLs.
- Use Redis Cluster or Sentinel for high availability.
- Monitor Redis using Prometheus, Grafana, and centralized logging.
- Automate deployments with Helm or Redis Operators for production-grade operations.