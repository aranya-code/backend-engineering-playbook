# Resource & Performance Issues

## Overview

Resource management is one of the most important aspects of running Kubernetes in production. Poor resource allocation can lead to slow applications, Pod evictions, scheduling failures, OOMKilled containers, CPU throttling, and unstable clusters.

This guide explains the most common resource and performance issues, how to diagnose them, and the best practices for optimizing Kubernetes workloads.

---

# Why Resource Issues Occur

Performance problems usually occur because of:

- Incorrect Resource Requests
- Incorrect Resource Limits
- Memory leaks
- High CPU utilization
- Missing autoscaling
- Node resource exhaustion
- Inefficient applications
- Uneven workload distribution

---

# High CPU Usage

## Symptoms

- Slow application
- High response time
- High CPU utilization

---

## Investigation

Check Pod CPU usage:

```bash
kubectl top pod
```

Check Node usage:

```bash
kubectl top node
```

Describe Pod:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Optimize application code.
- Increase CPU limits if appropriate.
- Configure Horizontal Pod Autoscaler.
- Investigate inefficient database queries.

---

# CPU Throttling

## Symptoms

Application is slow even though Pods are running.

---

## Common Causes

- CPU Limit too low
- Burst traffic
- Heavy background jobs

---

## Investigation

Review Resource Limits:

```bash
kubectl describe pod <pod-name>
```

Look for:

```yaml
resources:
  limits:
    cpu:
```

---

## Resolution

- Increase CPU Limit.
- Optimize CPU-intensive operations.
- Configure HPA.

---

# High Memory Usage

## Symptoms

- Increasing memory consumption
- Slow application
- OOMKilled

---

## Investigation

```bash
kubectl top pod
```

Describe Pod:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Increase memory limit.
- Investigate memory leaks.
- Reduce unnecessary caching.
- Optimize application logic.

---

# OOMKilled

## Symptoms

```text
Reason:

OOMKilled
```

---

## Common Causes

- Memory leak
- Memory Limit too low
- Large data processing

---

## Investigation

```bash
kubectl describe pod

kubectl top pod
```

---

## Resolution

- Increase memory limits.
- Optimize application memory usage.
- Review garbage collection behavior.

---

# Resource Requests Too High

## Symptoms

Pods remain Pending.

---

## Investigation

Review:

```yaml
resources:
  requests:
```

Example:

```yaml
cpu: 4

memory: 16Gi
```

---

## Resolution

Use realistic values.

Example:

```yaml
cpu: 250m

memory: 512Mi
```

---

# Resource Limits Too Low

## Symptoms

- Frequent restarts
- CPU throttling
- OOMKilled

---

## Investigation

```bash
kubectl describe pod
```

Review:

```yaml
limits:
```

---

## Resolution

Adjust limits according to production workload.

Monitor before increasing resources.

---

# Uneven Load Distribution

## Symptoms

One Pod handles most traffic.

Other Pods remain idle.

---

## Investigation

Check:

- Service configuration
- Session affinity
- Load balancer configuration

---

## Resolution

- Disable sticky sessions if unnecessary.
- Verify Service configuration.
- Configure HPA.

---

# Horizontal Pod Autoscaler Not Scaling

## Symptoms

CPU remains high.

Replica count never changes.

---

## Investigation

```bash
kubectl get hpa

kubectl describe hpa

kubectl top pod
```

---

## Possible Causes

- Metrics Server missing
- CPU Requests missing
- HPA misconfigured

---

## Resolution

- Install Metrics Server.
- Configure CPU Requests.
- Review HPA thresholds.

---

# Cluster Resources Exhausted

## Symptoms

Pods remain Pending.

---

## Investigation

```bash
kubectl top nodes

kubectl describe node
```

---

## Resolution

- Add Worker Nodes.
- Enable Cluster Autoscaler.
- Reduce unnecessary workloads.

---

# Frequent Pod Evictions

## Symptoms

```text
STATUS

Evicted
```

---

## Common Causes

- Memory pressure
- Disk pressure
- Node resource exhaustion

---

## Investigation

```bash
kubectl describe node
```

Review:

```text
Conditions
```

---

## Resolution

- Free node resources.
- Increase node capacity.
- Configure Resource Requests and Limits.

---

# Slow Application Response

## Symptoms

- High latency
- Slow API responses
- Timeout errors

---

## Investigation

Check:

- CPU usage
- Memory usage
- Database performance
- External APIs
- Network latency

---

## Resolution

- Optimize application code.
- Tune database queries.
- Scale horizontally.
- Cache frequently accessed data.

---

# Database Becoming the Bottleneck

## Symptoms

Application Pods scale successfully.

Performance remains poor.

---

## Investigation

Monitor:

- Database CPU
- Connection pool
- Query performance

---

## Resolution

- Optimize queries.
- Add indexes.
- Scale the database.
- Introduce caching.

Scaling application Pods alone will not resolve database bottlenecks.

---

# Resource & Performance Troubleshooting Workflow

```text
Application Slow
        │
        ▼
Check CPU
        │
        ▼
Check Memory
        │
        ▼
Review Requests & Limits
        │
        ▼
Check HPA
        │
        ▼
Check Node Resources
        │
        ▼
Check Database
        │
        ▼
Check External Services
        │
        ▼
Optimize & Scale
```

---

# Useful Commands

```bash
kubectl top pod

kubectl top node

kubectl describe pod <pod-name>

kubectl get hpa

kubectl describe hpa

kubectl get nodes

kubectl describe node <node-name>

kubectl get events
```

---

# Best Practices

- Configure Resource Requests for every container.
- Configure Resource Limits to prevent resource starvation.
- Monitor CPU and memory continuously.
- Enable Horizontal Pod Autoscaler.
- Enable Cluster Autoscaler for production clusters.
- Profile applications regularly to detect performance bottlenecks.
- Optimize databases before adding more application replicas.
- Use caching where appropriate to reduce backend load.

---

# Interview Tips

- Resource **Requests** determine scheduling, while **Limits** restrict runtime resource usage.
- High CPU does not always mean the application needs more replicas—it could indicate inefficient code.
- OOMKilled is caused by exceeding memory limits, not CPU limits.
- Scaling Pods does not solve database or external dependency bottlenecks.
- Always investigate resource usage before increasing infrastructure.

---

## Key Takeaways

- Most Kubernetes performance issues stem from improper resource allocation, inefficient application design, or infrastructure bottlenecks.
- Resource Requests, Resource Limits, and autoscaling work together to ensure stable and efficient workloads.
- `kubectl top`, `kubectl describe`, and `kubectl get hpa` are essential tools for diagnosing performance issues.
- A systematic approach to monitoring, profiling, and scaling helps maintain reliable and performant Kubernetes applications in production.