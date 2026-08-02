# Resource Requests and Limits

## Overview

Kubernetes allows you to define how much **CPU** and **memory** a container requires and how much it is allowed to consume. These resource constraints help the Kubernetes scheduler make intelligent placement decisions and prevent applications from consuming excessive resources.

Resource management is one of the most important aspects of running production workloads. Properly configured **Resource Requests** and **Limits** improve application stability, cluster utilization, and overall reliability.

---

## Why Resource Management Matters

Without resource constraints:

- One application can consume all available CPU.
- Memory leaks can crash an entire node.
- Critical applications may starve for resources.
- The scheduler cannot make optimal placement decisions.

Using Requests and Limits helps:

- Prevent resource contention
- Improve cluster stability
- Increase workload predictability
- Optimize hardware utilization
- Protect critical applications

---

## Resource Types

Kubernetes primarily manages two resources:

| Resource | Unit |
|----------|------|
| CPU | millicores (m) or cores |
| Memory | Mi, Gi |

Examples:

```text
CPU:
500m = 0.5 CPU
1000m = 1 CPU

Memory:
128Mi
512Mi
1Gi
4Gi
```

---

# Resource Requests

## Overview

A **Request** specifies the minimum amount of CPU and memory that Kubernetes guarantees to a container.

The scheduler uses requests when deciding which node can host a Pod.

Think of a request as:

> "This application needs at least this much resource."

---

## Example

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
```

This means:

- Reserve 0.5 CPU
- Reserve 256 MB of memory

Even if the application uses less, these resources are reserved for it.

---

## Scheduling Example

Suppose a node has:

```text
4 CPU
8 GB Memory
```

Pod requests:

```text
CPU: 1
Memory: 2 GB
```

The scheduler checks:

```text
Does the node have at least
1 CPU and 2 GB free?

YES → Schedule Pod
NO → Find another node
```

---

# Resource Limits

## Overview

A **Limit** specifies the maximum amount of CPU and memory a container may use.

Think of a limit as:

> "The application cannot exceed this amount."

---

## Example

```yaml
resources:
  limits:
    cpu: "1"
    memory: "512Mi"
```

The container may use:

- Up to 1 CPU
- Up to 512 MB memory

---

# Requests vs Limits

| Feature | Request | Limit |
|----------|----------|--------|
| Used by Scheduler | ✅ | ❌ |
| Minimum Guaranteed | ✅ | ❌ |
| Maximum Allowed | ❌ | ✅ |
| Can Exceed? | No | No |

---

## Complete Example

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"

  limits:
    cpu: "1"
    memory: "512Mi"
```

This means:

- Kubernetes reserves 0.5 CPU and 256 MiB.
- The application can burst up to 1 CPU and 512 MiB.

---

# CPU Limits

CPU is a **compressible resource**.

If a container exceeds its CPU limit:

- It is **throttled**.
- The container continues running.
- It receives less CPU time.

Example:

```text
Limit = 1 CPU

Application wants 2 CPU

↓

Kubernetes throttles CPU usage
```

The container is **not restarted**.

---

# Memory Limits

Memory is **not compressible**.

If a container exceeds its memory limit:

```text
Container exceeds limit

↓

OOM Killer

↓

Container terminated

↓

Restart (depending on restart policy)
```

Example:

```text
STATUS:
OOMKilled
```

This is one of the most common Kubernetes production issues.

---

# CPU Throttling

When CPU usage exceeds the configured limit:

```text
Requested:
2 CPUs

Allowed:
1 CPU

↓

Kernel throttles CPU
```

Symptoms include:

- Slow API responses
- Increased latency
- High response times

The container remains healthy but performs poorly.

---

# OOMKilled

OOM stands for:

```text
Out Of Memory
```

If a container exceeds its memory limit:

```text
Application

↓

Consumes too much RAM

↓

Kernel kills process

↓

Container restarts
```

Check with:

```bash
kubectl describe pod <pod-name>
```

Example:

```text
Reason:
OOMKilled
```

---

# Scheduler Decision

The scheduler only considers **Requests**, not Limits.

Example:

Node:

```text
CPU:
4

Memory:
8 GB
```

Pod Requests:

```text
CPU:
2

Memory:
4 GB
```

The Pod can be scheduled.

Even if the limit is larger.

---

# Quality of Service (QoS)

Kubernetes assigns Pods to QoS classes.

---

## Guaranteed

Requests equal Limits.

Example:

```yaml
requests:
  cpu: "1"
  memory: "1Gi"

limits:
  cpu: "1"
  memory: "1Gi"
```

Highest priority.

---

## Burstable

Requests are smaller than Limits.

Example:

```yaml
requests:
  cpu: "500m"

limits:
  cpu: "1"
```

Most production applications use this class.

---

## BestEffort

No Requests or Limits defined.

Example:

```yaml
resources: {}
```

Lowest priority.

These Pods are the first to be evicted when resources are scarce.

---

# Viewing Resource Usage

View resource requests:

```bash
kubectl describe pod <pod-name>
```

View node resources:

```bash
kubectl describe node
```

View live CPU and memory usage:

```bash
kubectl top pod
```

View node utilization:

```bash
kubectl top node
```

> **Note:** `kubectl top` requires the **Metrics Server** to be installed in the cluster.

---

# Resource Management Best Practices

- Always define CPU and memory requests.
- Always define resource limits for production workloads.
- Monitor actual resource usage before tuning values.
- Start with conservative requests and adjust based on metrics.
- Avoid setting limits too low, which can lead to throttling or OOM kills.
- Use the Burstable QoS class for most backend applications.
- Regularly review resource allocations to optimize cluster utilization.

---

# Common Problems

| Problem | Cause |
|---------|-------|
| Pending Pod | Requested resources unavailable |
| OOMKilled | Memory limit exceeded |
| High latency | CPU throttling |
| Node overload | Missing Requests |
| Frequent evictions | BestEffort Pods |

---

# Interview Tips

- Requests determine where a Pod can be scheduled.
- Limits determine how much CPU and memory a container may consume.
- CPU overuse results in throttling, not termination.
- Memory overuse results in **OOMKilled**.
- The scheduler considers Requests, not Limits.
- QoS classes are **Guaranteed**, **Burstable**, and **BestEffort**.
- Every production workload should define appropriate Requests and Limits.

---

## Key Takeaways

- Resource Requests reserve the minimum CPU and memory required by a container.
- Resource Limits cap the maximum CPU and memory a container can consume.
- CPU overuse causes throttling, while memory overuse results in container termination.
- The Kubernetes scheduler relies on Requests to place Pods on suitable nodes.
- Proper resource management improves application reliability, cluster efficiency, and workload stability.
- Configuring Requests and Limits is a fundamental best practice for running production-grade Kubernetes applications.