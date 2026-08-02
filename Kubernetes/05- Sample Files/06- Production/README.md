# Kubernetes Production Examples

## Overview

The **Production** folder brings together Kubernetes features that are commonly used in real-world production environments.

Unlike the previous sections, which focused on individual Kubernetes resources, this section demonstrates how multiple features work together to build highly available, scalable, secure, and maintainable applications.

These examples represent production best practices followed by organizations deploying applications on Kubernetes.

---

# Why This Section Matters

Deploying an application successfully is only the first step.

A production-ready Kubernetes application must also:

- Deploy without downtime
- Recover automatically from failures
- Scale based on demand
- Protect application availability
- Follow security best practices
- Support safe application upgrades
- Be easy to maintain and troubleshoot

This section focuses on those production concerns.

---

# Navigation

| Step | File | Purpose |
|------|------|---------|
| 01 | **01- Rolling-Update.yaml** | Learn Kubernetes' default deployment strategy for zero-downtime releases. |
| 02 | **02- Liveness-Readiness-Startup-Probes.yaml** | Configure production health checks for application reliability. |
| 03 | **03- Deployment-Strategy.md** | Compare deployment strategies and understand when to use each one. |
| 04 | **04- Production-Deployment.yaml** | Explore a production-ready Deployment manifest that combines Kubernetes best practices. |
| 05 | **05- Production-Stack-Architecture.md** | Understand how production Kubernetes resources interact to form a complete application stack. |

---

# Learning Path

Study the examples in the following order.

```text
Rolling Update
      │
      ▼
Health Probes
      │
      ▼
Deployment Strategies
      │
      ▼
Production Deployment
      │
      ▼
Production Stack Architecture
```

---

# Production Deployment Lifecycle

```text
Developer
     │
     ▼
Git Repository
     │
     ▼
CI Pipeline
     │
     ▼
Container Registry
     │
     ▼
CD Pipeline
     │
     ▼
Kubernetes Cluster
     │
     ▼
Rolling Update
     │
     ▼
Healthy Application
```

---

# Production Architecture

```text
                    Internet
                        │
                        ▼
                Cloud Load Balancer
                        │
                        ▼
              Ingress Controller
                        │
                        ▼
                    Ingress
                        │
                        ▼
                    Service
                        │
                        ▼
                  Deployment
            ┌─────────┼─────────┐
            ▼         ▼         ▼
          Pod-1     Pod-2     Pod-3
            │         │         │
            ├─────────┼─────────┤
            ▼         ▼         ▼
      ConfigMap    Secret      PVC
            │         │         │
            └─────────┼─────────┘
                      ▼
              Persistent Storage
```

---

# Production Features Covered

This section combines many Kubernetes production concepts, including:

- Rolling Updates
- Zero-Downtime Deployments
- Startup Probes
- Readiness Probes
- Liveness Probes
- Resource Requests & Limits
- Security Contexts
- ConfigMaps
- Secrets
- Persistent Storage
- Deployment Strategies
- Graceful Shutdown
- Pod Distribution
- High Availability

---

# Production Readiness Checklist

Before deploying to production, verify the following:

| Item | Status |
|------|:------:|
| Multiple Replicas | ✅ |
| Rolling Update Strategy | ✅ |
| Resource Requests | ✅ |
| Resource Limits | ✅ |
| Startup Probe | ✅ |
| Readiness Probe | ✅ |
| Liveness Probe | ✅ |
| ConfigMap | ✅ |
| Secret | ✅ |
| Persistent Storage (if required) | ✅ |
| Security Context | ✅ |
| Graceful Shutdown | ✅ |
| Pod Anti-Affinity | ✅ |
| TLS Enabled | ✅ |
| Monitoring & Logging | ✅ |

---

# What You'll Learn

After completing this section, you'll understand how to:

- Perform zero-downtime deployments
- Configure production health checks
- Compare deployment strategies
- Build production-grade Deployment manifests
- Design complete Kubernetes application architectures
- Apply production best practices

---

# Recommended Workflow

For each example:

1. Read the comments in the manifest or document.
2. Deploy the example in a test cluster.
3. Verify the deployed resources.
4. Simulate application updates.
5. Observe rollout behavior.
6. Test health probe failures.
7. Review rollback procedures.
8. Understand how each production feature contributes to application reliability.

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

Monitor Rollout

```bash
kubectl rollout status deployment <deployment-name>
```

View Rollout History

```bash
kubectl rollout history deployment <deployment-name>
```

Rollback Deployment

```bash
kubectl rollout undo deployment <deployment-name>
```

Describe Deployment

```bash
kubectl describe deployment <deployment-name>
```

View Events

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

View Logs

```bash
kubectl logs <pod-name>
```

---


# Best Practices

- Prefer Rolling Updates for most stateless applications.
- Configure Startup, Readiness, and Liveness Probes for every production workload.
- Use immutable container image tags instead of `latest`.
- Define Resource Requests and Limits for all containers.
- Externalize configuration using ConfigMaps and Secrets.
- Run multiple replicas for high availability.
- Configure graceful shutdown to avoid dropped requests.
- Monitor rollouts and application health continuously.
- Design deployments with security, scalability, and maintainability in mind.

---

## Key Takeaways

- Production Kubernetes deployments require more than just running Pods—they require strategies for reliability, scalability, security, and maintainability.
- Rolling Updates and health probes enable safe, zero-downtime application deployments.
- Production-grade manifests combine multiple Kubernetes features into a cohesive deployment model.
- Understanding deployment strategies helps teams choose the right release approach for different business requirements.
- This section brings together the concepts from the rest of the playbook into practical, production-focused examples suitable for real-world Kubernetes environments.