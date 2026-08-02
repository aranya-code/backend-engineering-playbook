# Kubernetes Scaling Examples

## Overview

The **Scaling** folder demonstrates how Kubernetes automatically manages application capacity, resource allocation, and availability.

Modern Kubernetes applications must handle changing workloads efficiently. Instead of manually increasing replicas or adding infrastructure, Kubernetes provides several scaling mechanisms that automatically respond to traffic, resource utilization, and maintenance events.

This section covers CPU and memory management, horizontal scaling, vertical scaling, and high availability during cluster maintenance.

---

# Why This Section Matters

Applications rarely experience constant traffic.

During peak hours, applications require more resources, while during quiet periods, excess resources increase infrastructure costs.

Kubernetes solves these challenges by providing automatic scaling mechanisms that:

- Improve application availability
- Reduce infrastructure costs
- Prevent resource starvation
- Optimize cluster utilization
- Maintain application uptime during maintenance

Understanding these concepts is essential for designing production-ready Kubernetes workloads.

---

# Navigation

| Step | File | Purpose |
|------|------|---------|
| 01 | **01- Resource-Requests-Limits.yaml** | Learn how Requests and Limits control scheduling and resource usage. |
| 02 | **02- Horizontal-Pod-Autoscaler.yaml** | Automatically scale Pods based on CPU utilization. |
| 03 | **03- Vertical-Pod-Autoscaler.yaml** | Automatically optimize CPU and Memory Requests. |
| 04 | **04- Pod-Disruption-Budget.yaml** | Maintain application availability during node maintenance and upgrades. |

---

# Learning Path

Study these examples in the following order.

```text
Resource Requests & Limits
             │
             ▼
Horizontal Pod Autoscaler
             │
             ▼
Vertical Pod Autoscaler
             │
             ▼
Pod Disruption Budget
```

---

# Scaling Architecture

```text
                 Users
                   │
                   ▼
             Load Balancer
                   │
                   ▼
              Deployment
                   │
        ┌──────────┼──────────┐
        ▼                     ▼
Resource Requests        Horizontal
   & Limits           Pod Autoscaler
        │                     │
        ▼                     ▼
   Scheduler            Scale Pods
        │
        ▼
 Running Pods
        │
        ▼
Vertical Pod Autoscaler
        │
        ▼
Optimize CPU & Memory
```

---

# Kubernetes Scaling Components

| Component | Scales | Purpose |
|-----------|--------|---------|
| Resource Requests | Minimum resources | Scheduling decisions |
| Resource Limits | Maximum resources | Prevent resource abuse |
| Horizontal Pod Autoscaler | Number of Pods | Handle changing traffic |
| Vertical Pod Autoscaler | CPU & Memory | Optimize resource allocation |
| Pod Disruption Budget | Availability | Protect workloads during maintenance |

---

# Horizontal vs Vertical Scaling

## Horizontal Scaling

Increase or decrease the number of Pods.

```text
2 Pods

↓

5 Pods

↓

10 Pods
```

Best for:

- APIs
- Web Applications
- Microservices
- Stateless workloads

---

## Vertical Scaling

Increase or decrease resources assigned to each Pod.

```text
CPU

200m

↓

500m


Memory

256Mi

↓

1Gi
```

Best for:

- Databases
- Stateful applications
- Legacy workloads
- Applications with predictable traffic

---

# Pod Availability

```text
Deployment

3 Replicas

        │

        ▼

Pod Disruption Budget

minAvailable = 2

        │

        ▼

Node Maintenance

        │

        ▼

Only One Pod

Can Be Evicted
```

---

# What You'll Learn

After completing this section, you'll understand how to:

- Configure CPU Requests
- Configure Memory Limits
- Automatically scale applications
- Optimize resource utilization
- Protect workloads during maintenance
- Build highly available applications
- Design production-ready scaling strategies

---

# Production Scaling Strategy

A typical production deployment uses multiple scaling mechanisms together.

```text
Users
   │
   ▼
Ingress
   │
   ▼
Deployment
   │
   ├───────────────┐
   ▼               ▼
HPA             Resource Limits
   │               │
   ▼               ▼
Pods        CPU & Memory
   │
   ▼
PDB Protects
Availability
```

---

# Recommended Workflow

For each example:

1. Read the comments in the YAML file.
2. Deploy the resource.
3. Verify the resource creation.
4. Generate application load where applicable.
5. Observe scaling behavior.
6. Inspect resource usage.
7. Modify configuration values.
8. Observe how Kubernetes responds.

---

# Frequently Used Commands

View Deployments

```bash
kubectl get deployment
```

View Pods

```bash
kubectl get pods
```

View HPA

```bash
kubectl get hpa
```

View Resource Usage

```bash
kubectl top pod
```

View Node Usage

```bash
kubectl top node
```

Describe a Pod

```bash
kubectl describe pod <pod-name>
```

View Pod Disruption Budgets

```bash
kubectl get pdb
```

Describe a PDB

```bash
kubectl describe pdb <pdb-name>
```

---

# Best Practices

- Always configure CPU and Memory Requests.
- Define realistic Resource Limits for every production container.
- Use Horizontal Pod Autoscaler for stateless applications with fluctuating traffic.
- Consider Vertical Pod Autoscaler for workloads with predictable resource requirements.
- Protect critical applications using Pod Disruption Budgets.
- Monitor resource utilization continuously and adjust scaling policies based on real workload patterns.
- Test scaling behavior under load before deploying to production.

---

## Key Takeaways

- Kubernetes provides multiple scaling mechanisms that work together to improve performance, availability, and resource efficiency.
- Resource Requests and Limits determine how workloads are scheduled and constrained.
- Horizontal Pod Autoscaler adjusts the number of Pods based on resource utilization.
- Vertical Pod Autoscaler optimizes CPU and Memory allocations for individual Pods.
- Pod Disruption Budgets help maintain application availability during planned maintenance and cluster operations.
- Combining these features enables resilient, cost-effective, and production-ready Kubernetes deployments.