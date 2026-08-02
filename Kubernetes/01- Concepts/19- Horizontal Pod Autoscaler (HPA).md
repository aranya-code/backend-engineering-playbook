# Horizontal Pod Autoscaler (HPA)

## Overview

The **Horizontal Pod Autoscaler (HPA)** is a Kubernetes feature that automatically scales the number of Pod replicas based on observed resource utilization or custom metrics.

Instead of manually increasing or decreasing replicas, HPA continuously monitors application load and adjusts the replica count to maintain performance while optimizing resource usage.

HPA is one of the core autoscaling mechanisms in Kubernetes and is widely used in production environments to handle varying workloads.

---

## Why Horizontal Autoscaling Matters

Applications rarely receive a constant amount of traffic.

For example:

- An e-commerce website experiences heavy traffic during sales.
- A banking application sees peak usage during business hours.
- An API receives sudden bursts of requests after a marketing campaign.

Without autoscaling:

- High traffic may overwhelm the application.
- Low traffic wastes computing resources.

HPA solves this problem by automatically adjusting the number of running Pods.

---

## How HPA Works

The Horizontal Pod Autoscaler continuously monitors application metrics.

When resource usage exceeds a configured threshold:

- Kubernetes creates additional Pods.

When usage decreases:

- Kubernetes removes unnecessary Pods.

```text
          High CPU Usage
                 │
                 ▼
      Horizontal Pod Autoscaler
                 │
                 ▼
      Increase Pod Replicas
                 │
                 ▼
     Deployment Updated Automatically
```

---

## Scaling Example

Suppose a Deployment initially runs:

```text
3 Pods
```

Traffic increases.

Average CPU usage becomes:

```text
85%
```

The HPA target is:

```text
60%
```

Kubernetes automatically scales:

```text
3 Pods

↓

5 Pods

↓

8 Pods
```

As traffic decreases:

```text
8 Pods

↓

5 Pods

↓

3 Pods
```

---

## HPA Architecture

```text
Metrics Server
        │
        ▼
Horizontal Pod Autoscaler
        │
        ▼
Deployment / ReplicaSet
        │
        ▼
Pods
```

The **Metrics Server** collects CPU and memory usage.

The HPA controller periodically reads these metrics and adjusts the replica count.

---

## Requirements

Before using HPA, your cluster should have:

- Metrics Server installed
- CPU and memory Requests configured
- A Deployment, ReplicaSet, or StatefulSet
- Kubernetes Metrics API enabled

Without the Metrics Server, HPA cannot calculate utilization.

---

## Basic HPA YAML

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler

metadata:
  name: api-hpa

spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api

  minReplicas: 2
  maxReplicas: 10

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

---

## Explanation

| Field | Description |
|--------|-------------|
| scaleTargetRef | Resource being scaled |
| minReplicas | Minimum number of Pods |
| maxReplicas | Maximum number of Pods |
| averageUtilization | Target CPU utilization |

---

## Scaling Decision

Example:

```text
Current Pods:
4

Target CPU:
60%

Current CPU:
90%
```

HPA calculates:

```text
More Pods Required

↓

Scale to 6 Pods
```

---

## Scaling Down

When utilization decreases:

```text
Current Pods:
8

CPU:
20%

↓

Scale Down

↓

4 Pods
```

Kubernetes performs scale-down gradually to avoid instability.

---

## CPU-Based Autoscaling

The most common configuration.

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
```

Ideal for:

- REST APIs
- Backend services
- Microservices

---

## Memory-Based Autoscaling

HPA can also monitor memory.

```yaml
metrics:
- type: Resource
  resource:
    name: memory
```

Useful for:

- Caching applications
- JVM applications
- Data processing services

---

## Custom Metrics

Production systems often scale using business metrics.

Examples:

- Requests per second
- Queue length
- Kafka lag
- Active sessions
- Response time

Example:

```text
Queue Size > 500

↓

Scale Workers
```

Custom metrics require additional components such as Prometheus Adapter.

---

## Viewing HPA

List autoscalers:

```bash
kubectl get hpa
```

Example:

```text
NAME      REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS

api-hpa   Deployment/backend-api  45%/60%   2         10        3
```

---

Describe an autoscaler:

```bash
kubectl describe hpa api-hpa
```

---

## HPA vs Manual Scaling

Manual scaling:

```bash
kubectl scale deployment backend-api --replicas=5
```

HPA:

```text
Automatically adjusts replicas

↓

No manual intervention
```

---

## HPA Limitations

HPA cannot solve every scaling problem.

It does **not**:

- Add new worker nodes
- Scale persistent storage
- Scale databases automatically

It only changes the number of Pod replicas.

---

## Interaction with Cluster Autoscaler

When HPA creates more Pods but no nodes have enough resources:

```text
HPA

↓

More Pods

↓

Pods Pending

↓

Cluster Autoscaler Adds Nodes

↓

Pods Scheduled
```

HPA and Cluster Autoscaler often work together in production environments.

---

## Common Problems

| Problem | Possible Cause |
|----------|----------------|
| HPA not scaling | Metrics Server missing |
| Pods remain Pending | Cluster lacks resources |
| No CPU metrics | Requests not configured |
| Frequent scaling | Thresholds too aggressive |
| Slow scaling | Stabilization window |

---

## Best Practices

- Always configure CPU Requests before enabling HPA.
- Set realistic minimum and maximum replica counts.
- Monitor application performance after scaling.
- Avoid overly aggressive scaling thresholds.
- Combine HPA with Cluster Autoscaler for production clusters.
- Use custom metrics when CPU usage is not a good indicator of load.
- Test autoscaling under realistic traffic conditions.

---

## Interview Tips

- HPA scales the **number of Pods**, not the size of Pods.
- HPA commonly uses CPU utilization but also supports memory and custom metrics.
- The Metrics Server is required for CPU and memory-based autoscaling.
- HPA works with Deployments, ReplicaSets, and StatefulSets.
- HPA does **not** create new cluster nodes—that is the responsibility of the Cluster Autoscaler.
- Resource Requests should be configured for HPA to make accurate scaling decisions.

---

## Key Takeaways

- Horizontal Pod Autoscaler automatically adjusts the number of Pod replicas based on observed metrics.
- HPA improves application availability during traffic spikes while reducing resource usage during low demand.
- CPU utilization is the most common scaling metric, but memory and custom metrics are also supported.
- The Metrics Server is required for resource-based autoscaling.
- HPA is a fundamental production feature for running scalable and resilient Kubernetes applications.
```