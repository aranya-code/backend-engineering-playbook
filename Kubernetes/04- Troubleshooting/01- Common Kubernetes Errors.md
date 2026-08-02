# Common Kubernetes Errors

## Overview

Kubernetes provides detailed status messages and error conditions that help diagnose problems with Pods, Deployments, Services, networking, and storage. Understanding these common errors is essential for quickly identifying root causes and restoring applications in production.

This guide explains the most frequently encountered Kubernetes errors, why they occur, how to investigate them, and common ways to resolve them.

---

# Why This Topic Matters

Most Kubernetes production issues fall into a small number of recurring error categories.

Learning these errors helps you:

- Diagnose application failures faster
- Reduce production downtime
- Improve troubleshooting skills
- Prepare for Kubernetes interviews
- Understand Kubernetes event messages

---

# Error Categories

| Category | Examples |
|----------|----------|
| Scheduling | Pending, FailedScheduling |
| Image | ErrImagePull, ImagePullBackOff |
| Startup | ContainerCreating, CreateContainerError |
| Runtime | CrashLoopBackOff |
| Configuration | CreateContainerConfigError |
| Resource | OOMKilled, Evicted |
| Networking | Service unreachable, DNS failures |
| Storage | PVC Pending, Volume Mount Failed |

---

# Pending

## Description

The Pod has been accepted by Kubernetes but has not yet started running.

Example:

```text
STATUS

Pending
```

---

## Common Causes

- Insufficient CPU
- Insufficient Memory
- No available Worker Node
- PVC not bound
- Node Affinity mismatch
- Taints and Tolerations

---

## How to Investigate

```bash
kubectl describe pod <pod-name>

kubectl get events
```

---

## Common Fixes

- Add more cluster resources
- Reduce resource requests
- Fix scheduling rules
- Verify Persistent Volumes
- Check node availability

---

# CrashLoopBackOff

## Description

The container starts successfully but repeatedly crashes.

```text
Running

↓

Crash

↓

Restart

↓

Crash

↓

Restart
```

Eventually Kubernetes reports:

```text
CrashLoopBackOff
```

---

## Common Causes

- Application exceptions
- Missing environment variables
- Invalid configuration
- Database connection failures
- Startup script errors
- Failed health checks

---

## How to Investigate

```bash
kubectl logs <pod-name>

kubectl describe pod <pod-name>
```

---

## Common Fixes

- Review application logs
- Verify ConfigMaps
- Verify Secrets
- Check database connectivity
- Fix application startup errors

---

# ErrImagePull

## Description

Kubernetes failed to download the container image.

Example:

```text
ErrImagePull
```

---

## Common Causes

- Incorrect image name
- Incorrect image tag
- Private registry authentication failure
- Registry unavailable

---

## How to Investigate

```bash
kubectl describe pod <pod-name>
```

Look for image pull events.

---

## Common Fixes

- Verify image name
- Verify tag
- Configure imagePullSecrets
- Check registry credentials

---

# ImagePullBackOff

## Description

Kubernetes repeatedly attempts to pull the image after previous failures.

Example:

```text
ErrImagePull

↓

Retry

↓

Retry

↓

ImagePullBackOff
```

---

## Common Causes

- Invalid image
- Registry unavailable
- Authentication failure
- Network connectivity issues

---

## How to Investigate

```bash
kubectl describe pod <pod-name>
```

---

## Common Fixes

- Verify registry access
- Correct image reference
- Configure authentication
- Test network connectivity

---

# ContainerCreating

## Description

The Pod has been scheduled, but Kubernetes is still preparing the container.

Example:

```text
STATUS

ContainerCreating
```

---

## Common Causes

- Image downloading
- Volume attachment
- Secret mounting
- ConfigMap mounting
- Slow storage provisioning

---

## How to Investigate

```bash
kubectl describe pod <pod-name>
```

---

## Common Fixes

- Wait for image download
- Verify storage availability
- Verify ConfigMaps
- Verify Secrets

---

# CreateContainerConfigError

## Description

The container cannot start because its configuration is invalid.

---

## Common Causes

- Missing ConfigMap
- Missing Secret
- Invalid environment variables
- Incorrect volume configuration

---

## How to Investigate

```bash
kubectl describe pod <pod-name>
```

---

## Common Fixes

- Create missing ConfigMap
- Create missing Secret
- Correct environment variables
- Verify volume mounts

---

# CreateContainerError

## Description

The container runtime failed to create the container.

---

## Common Causes

- Invalid command
- Invalid entrypoint
- Missing executable
- Invalid image

---

## How to Investigate

```bash
kubectl logs <pod-name>

kubectl describe pod <pod-name>
```

---

## Common Fixes

- Verify Docker image
- Verify startup command
- Check entrypoint
- Rebuild image if necessary

---

# OOMKilled

## Description

The Linux kernel terminated the container because it exceeded its memory limit.

Example:

```text
Reason:

OOMKilled
```

---

## Common Causes

- Memory leak
- Memory limit too low
- Large workloads
- Inefficient application

---

## How to Investigate

```bash
kubectl describe pod <pod-name>

kubectl top pod
```

---

## Common Fixes

- Increase memory limit
- Optimize application memory usage
- Investigate memory leaks

---

# Evicted

## Description

The Pod was removed from the node because the node ran out of resources.

Example:

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

## How to Investigate

```bash
kubectl describe node

kubectl describe pod <pod-name>
```

---

## Common Fixes

- Free node resources
- Increase node capacity
- Configure Resource Requests and Limits

---

# FailedScheduling

## Description

The Scheduler cannot find a suitable Worker Node.

---

## Common Causes

- No available resources
- Node selector mismatch
- Taints
- Affinity rules
- Storage constraints

---

## How to Investigate

```bash
kubectl describe pod <pod-name>
```

Look under **Events**.

---

## Common Fixes

- Add Worker Nodes
- Adjust scheduling rules
- Reduce resource requests
- Review taints and tolerations

---

# Error Investigation Workflow

```text
Check Pod Status
        │
        ▼
Describe Pod
        │
        ▼
Review Events
        │
        ▼
Check Logs
        │
        ▼
Verify Configuration
        │
        ▼
Check Resources
        │
        ▼
Check Networking
        │
        ▼
Verify Storage
```

---

# Most Useful Debugging Commands

```bash
kubectl get pods

kubectl describe pod <pod-name>

kubectl logs <pod-name>

kubectl logs <pod-name> --previous

kubectl get events

kubectl top pod

kubectl get pvc

kubectl get svc

kubectl get endpoints

kubectl rollout status deployment
```

---

# Best Practices

- Always check Events before making changes.
- Review application logs before restarting Pods.
- Configure Resource Requests and Limits.
- Use Readiness and Liveness Probes.
- Store configuration in ConfigMaps and Secrets.
- Monitor cluster resource usage.
- Avoid hardcoding image tags such as `latest` in production.

---

# Interview Tips

- Understand the difference between **ErrImagePull** and **ImagePullBackOff**.
- Know why **CrashLoopBackOff** occurs and how to investigate it.
- Be able to explain why **OOMKilled** happens.
- Mention `kubectl describe`, `kubectl logs`, and `kubectl get events` when discussing troubleshooting.
- Follow a structured debugging process instead of guessing.

---

## Key Takeaways

- Kubernetes status messages provide valuable clues about application and cluster health.
- Most production issues can be categorized into scheduling, image, runtime, configuration, resource, networking, or storage problems.
- `kubectl describe`, `kubectl logs`, and `kubectl get events` are the primary tools for diagnosing Kubernetes issues.
- Following a consistent troubleshooting workflow helps identify root causes efficiently and minimizes production downtime.
```