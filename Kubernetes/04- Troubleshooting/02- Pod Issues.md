# Pod Issues

## Overview

Pods are the smallest deployable units in Kubernetes and are the foundation of every application running in a cluster. When applications fail, the first place to investigate is usually the Pod.

This guide explains the most common Pod-related issues, how to diagnose them, and the steps to resolve them using Kubernetes commands and best practices.

---

# Why Pod Issues Occur

Pod failures commonly result from:

- Application crashes
- Invalid container images
- Scheduling failures
- Configuration errors
- Failed health probes
- Resource exhaustion
- Storage issues
- Networking problems

Understanding these issues helps reduce troubleshooting time in production environments.

---

# Pod Stuck in Pending

## Symptoms

```text
STATUS

Pending
```

The Pod has been accepted by Kubernetes but has not been scheduled to a Worker Node.

---

## Possible Causes

- Insufficient CPU
- Insufficient Memory
- Node Selector mismatch
- Taints and Tolerations
- Persistent Volume unavailable
- Node Affinity rules

---

## Investigation

Describe the Pod:

```bash
kubectl describe pod <pod-name>
```

Check events:

```bash
kubectl get events
```

View node resources:

```bash
kubectl describe node <node-name>
```

---

## Resolution

- Add more cluster resources.
- Reduce CPU or memory requests.
- Fix scheduling rules.
- Verify Persistent Volumes.
- Remove invalid node constraints.

---

# Pod Stuck in ContainerCreating

## Symptoms

```text
STATUS

ContainerCreating
```

The Pod has been scheduled, but Kubernetes is still preparing the container.

---

## Possible Causes

- Image download in progress
- Secret mounting
- ConfigMap mounting
- Persistent Volume attachment
- Slow storage backend

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Look under **Events**.

---

## Resolution

- Verify image accessibility.
- Check ConfigMaps.
- Verify Secrets.
- Confirm PVC is bound.
- Wait for storage provisioning if necessary.

---

# Pod Stuck in Terminating

## Symptoms

```text
STATUS

Terminating
```

The Pod is taking longer than expected to shut down.

---

## Possible Causes

- Application ignoring SIGTERM
- Hanging processes
- Finalizers
- Volume unmount delays

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Check finalizers:

```bash
kubectl get pod <pod-name> -o yaml
```

---

## Resolution

- Ensure the application handles SIGTERM.
- Reduce long shutdown operations.
- Remove unnecessary finalizers if appropriate.
- Force delete only as a last resort:

```bash
kubectl delete pod <pod-name> --grace-period=0 --force
```

---

# Pod Restarting Frequently

## Symptoms

```text
RESTARTS

15
```

Restart count keeps increasing.

---

## Possible Causes

- Application crash
- Failed Liveness Probe
- OOMKilled
- Missing dependencies
- Startup failure

---

## Investigation

Current logs:

```bash
kubectl logs <pod-name>
```

Previous container logs:

```bash
kubectl logs <pod-name> --previous
```

Describe the Pod:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Review application logs.
- Verify configuration.
- Fix probe settings.
- Increase resource limits if necessary.

---

# Pod Not Ready

## Symptoms

```text
READY

0/1
```

The container is running but not receiving traffic.

---

## Possible Causes

- Readiness Probe failure
- Application still starting
- Database unavailable
- External dependency unavailable

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Check Readiness Probe events.

---

## Resolution

- Verify application startup.
- Fix Readiness Probe configuration.
- Ensure dependent services are available.
- Increase startup delay if required.

---

# Init Container Failure

## Symptoms

```text
Init:CrashLoopBackOff
```

Main application containers never start.

---

## Possible Causes

- Invalid initialization script
- Database unavailable
- Missing Secret
- Missing ConfigMap

---

## Investigation

List containers:

```bash
kubectl describe pod <pod-name>
```

View init container logs:

```bash
kubectl logs <pod-name> -c <init-container-name>
```

---

## Resolution

- Fix initialization logic.
- Verify dependencies.
- Correct ConfigMaps or Secrets.
- Ensure external services are reachable.

---

# Liveness Probe Failure

## Symptoms

Container keeps restarting.

Events:

```text
Liveness probe failed
```

---

## Possible Causes

- Wrong endpoint
- Application freeze
- Timeout too low
- Startup taking too long

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Review probe configuration.

---

## Resolution

- Correct the health endpoint.
- Increase timeout values.
- Configure a Startup Probe.
- Optimize application startup.

---

# Readiness Probe Failure

## Symptoms

Pod is running but not receiving traffic.

---

## Possible Causes

- Database unavailable
- Application initialization incomplete
- Health endpoint failure

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Fix application readiness.
- Verify external dependencies.
- Adjust probe thresholds.

---

# Startup Probe Failure

## Symptoms

Application repeatedly restarts during initialization.

---

## Possible Causes

- Slow application startup
- Heavy initialization tasks
- Startup timeout too short

---

## Resolution

Configure a Startup Probe with appropriate values.

Example:

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

---

# Pod Cannot Access Another Service

## Possible Causes

- Incorrect Service name
- DNS issue
- Wrong namespace
- Network Policy
- Service selector mismatch

---

## Investigation

Check Services:

```bash
kubectl get svc
```

Check Endpoints:

```bash
kubectl get endpoints
```

Verify DNS:

```bash
kubectl exec -it <pod-name> -- nslookup <service-name>
```

---

## Resolution

- Verify Service name.
- Verify namespace.
- Check selectors.
- Review Network Policies.

---

# Pod Uses Too Much CPU

## Symptoms

Application responds slowly.

---

## Investigation

```bash
kubectl top pod
```

Review Resource Limits:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Increase CPU limit if appropriate.
- Optimize application code.
- Configure Horizontal Pod Autoscaler.

---

# Pod Uses Too Much Memory

## Symptoms

```text
OOMKilled
```

---

## Investigation

```bash
kubectl top pod

kubectl describe pod <pod-name>
```

---

## Resolution

- Increase memory limit.
- Fix memory leaks.
- Optimize caching.
- Tune application settings.

---

# Pod Troubleshooting Workflow

```text
Pod Status
      │
      ▼
Describe Pod
      │
      ▼
Check Events
      │
      ▼
View Logs
      │
      ▼
Verify Probes
      │
      ▼
Verify Resources
      │
      ▼
Verify Storage
      │
      ▼
Verify Networking
      │
      ▼
Resolve Root Cause
```

---

# Useful Commands

```bash
kubectl get pods

kubectl describe pod <pod-name>

kubectl logs <pod-name>

kubectl logs <pod-name> --previous

kubectl top pod

kubectl exec -it <pod-name> -- sh

kubectl get events

kubectl get pvc

kubectl get svc

kubectl get endpoints
```

---

# Best Practices

- Always inspect Pod events before making changes.
- Check previous logs for restarting containers.
- Configure Resource Requests and Limits.
- Use Readiness, Liveness, and Startup Probes correctly.
- Keep Pods stateless whenever possible.
- Store configuration in ConfigMaps and Secrets.
- Monitor restart counts and resource usage.

---

# Interview Tips

- A Pod in the **Running** state is not necessarily **Ready**.
- Always mention `kubectl describe` and `kubectl logs` when discussing Pod troubleshooting.
- Understand the differences between Pending, Running, CrashLoopBackOff, and OOMKilled.
- Explain a structured troubleshooting workflow instead of suggesting random fixes.

---

## Key Takeaways

- Most Kubernetes application issues originate at the Pod level and can be diagnosed using Pod status, events, and logs.
- Understanding common Pod states and health probe failures helps quickly identify root causes.
- `kubectl describe`, `kubectl logs`, and `kubectl top` are essential tools for Pod troubleshooting.
- A systematic troubleshooting approach reduces downtime and improves production reliability.
```