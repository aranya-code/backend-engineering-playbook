# Scenario Based Questions

## Overview

Scenario-based questions are designed to evaluate how you approach real-world Kubernetes problems rather than simply testing theoretical knowledge. Interviewers want to understand your troubleshooting process, decision-making, and ability to design reliable, scalable, and production-ready Kubernetes deployments.

These questions are commonly asked in Backend Engineer, DevOps Engineer, Platform Engineer, Site Reliability Engineer (SRE), and Cloud Engineer interviews.

---

# Why These Questions Matter

Scenario-based interviews assess your ability to:

- Troubleshoot production issues
- Design scalable architectures
- Improve application reliability
- Optimize Kubernetes resources
- Handle deployment failures
- Think systematically under pressure

When answering these questions:

- Explain your thought process.
- Mention the Kubernetes resources involved.
- Describe the commands you would use.
- Explain why your solution works.

---

# Scenario 1

## Your Pod is stuck in the **Pending** state. How would you troubleshoot it?

### Answer

My troubleshooting process would be:

```text
Check Pod Status

↓

Describe Pod

↓

Review Events

↓

Verify Resources

↓

Check Node Status

↓

Check PVC

↓

Check Scheduling Rules
```

Commands:

```bash
kubectl get pods

kubectl describe pod <pod-name>

kubectl get events

kubectl get nodes
```

Common causes:

- Insufficient CPU
- Insufficient Memory
- Node Affinity mismatch
- Missing Persistent Volume
- Taints and Tolerations

---

# Scenario 2

## A Pod keeps restarting with **CrashLoopBackOff**.

### Answer

First, inspect the Pod:

```bash
kubectl describe pod <pod-name>

kubectl logs <pod-name>
```

Things to verify:

- Application startup errors
- Environment variables
- ConfigMaps
- Secrets
- Database connectivity
- Liveness Probe
- Startup Probe

I would avoid restarting Pods immediately without identifying the root cause.

---

# Scenario 3

## Your application is deployed successfully, but users cannot access it.

### Answer

I would troubleshoot in this order:

```text
Pod Running?

↓

Service Exists?

↓

Endpoints Available?

↓

Ingress Working?

↓

DNS Correct?

↓

Application Listening?
```

Commands:

```bash
kubectl get pods

kubectl get svc

kubectl get endpoints

kubectl get ingress
```

---

# Scenario 4

## Your Service has no Endpoints.

### Answer

This usually indicates a selector mismatch.

Check:

```bash
kubectl get svc

kubectl get pods --show-labels
```

Verify that:

```yaml
selector:
  app: backend
```

matches the Pod labels.

Without matching labels, the Service cannot route traffic.

---

# Scenario 5

## A new deployment fails after release.

### Answer

My approach:

```text
Check Rollout

↓

Describe Deployment

↓

Inspect Events

↓

Check Pod Logs

↓

Verify Probes

↓

Rollback if Necessary
```

Commands:

```bash
kubectl rollout status deployment backend

kubectl describe deployment backend

kubectl logs <pod-name>
```

If required:

```bash
kubectl rollout undo deployment backend
```

---

# Scenario 6

## One Pod is receiving high CPU usage while others remain idle.

### Answer

Possible causes:

- Session affinity
- Uneven traffic distribution
- Poor application load balancing
- Sticky sessions

Check:

```bash
kubectl top pod
```

Verify:

- Service configuration
- HPA configuration
- Application load balancing

---

# Scenario 7

## A Deployment should have five replicas, but only three are running.

### Answer

Possible reasons:

- Insufficient cluster resources
- Pending Pods
- Failed Pods
- Scheduling issues

Commands:

```bash
kubectl get deployment

kubectl get rs

kubectl get pods

kubectl describe deployment
```

---

# Scenario 8

## Your application suddenly starts throwing database connection errors.

### Answer

Check:

- Database Pod
- Service
- DNS resolution
- Secret values
- Network policies

Commands:

```bash
kubectl logs

kubectl get svc

kubectl exec
```

Test:

```bash
nslookup database-service
```

---

# Scenario 9

## Users report intermittent failures during deployment.

### Answer

Possible reasons:

- Missing Readiness Probe
- Incorrect rolling update settings
- Pods receiving traffic before startup

Verify:

```yaml
readinessProbe
```

Review:

```yaml
maxUnavailable

maxSurge
```

---

# Scenario 10

## Your Pods are frequently getting **OOMKilled**.

### Answer

Check:

```bash
kubectl describe pod

kubectl top pod
```

Possible causes:

- Low memory limit
- Memory leak
- Poor application optimization

Solutions:

- Increase memory limits
- Optimize application memory usage
- Profile the application

---

# Scenario 11

## HPA is not scaling your application.

### Answer

Verify:

- Metrics Server installed
- CPU Requests configured
- HPA status
- Current CPU utilization

Commands:

```bash
kubectl get hpa

kubectl describe hpa

kubectl top pod
```

---

# Scenario 12

## An Ingress returns HTTP 404.

### Answer

Check:

- Ingress rules
- Backend Service
- Service Port
- Hostname
- Path

Commands:

```bash
kubectl get ingress

kubectl describe ingress
```

---

# Scenario 13

## Pods cannot pull images from a private registry.

### Answer

Possible causes:

- Missing imagePullSecret
- Invalid credentials
- Wrong registry URL
- Wrong image tag

Verify:

```bash
kubectl describe pod
```

---

# Scenario 14

## A Persistent Volume Claim remains in Pending state.

### Answer

Check:

```bash
kubectl get pvc

kubectl get pv

kubectl get storageclass
```

Possible causes:

- No matching PV
- Missing StorageClass
- Incorrect access mode
- Capacity mismatch

---

# Scenario 15

## A Worker Node suddenly goes offline.

### Answer

If Pods belong to a Deployment:

```text
Node Failure

↓

Pods Lost

↓

ReplicaSet

↓

New Pods Created

↓

Healthy Node
```

Kubernetes automatically restores the desired state.

---

# Scenario 16

## Your application needs to handle 10× more traffic during a sale event.

### Answer

I would:

- Configure HPA
- Enable Cluster Autoscaler
- Configure Resource Requests
- Configure Resource Limits
- Monitor CPU and Memory
- Verify LoadBalancer capacity

---

# Scenario 17

## How would you deploy a new version without downtime?

### Answer

I would use:

- Deployment
- Rolling Update
- Readiness Probe
- Liveness Probe

Verify rollout:

```bash
kubectl rollout status deployment
```

Rollback if necessary:

```bash
kubectl rollout undo deployment
```

---

# Scenario 18

## Your application works locally but fails in Kubernetes.

### Answer

Things to verify:

- Environment variables
- ConfigMaps
- Secrets
- Service names
- DNS
- Container ports
- Resource limits

Review:

```bash
kubectl logs

kubectl describe pod
```

---

# Scenario 19

## How would you debug a production Kubernetes issue?

### Answer

My debugging workflow:

```text
Check Resource Status

↓

Describe Resource

↓

Review Events

↓

Inspect Logs

↓

Verify Configuration

↓

Check Networking

↓

Check Storage

↓

Review Metrics

↓

Rollback if Needed
```

This systematic approach helps identify issues efficiently without making assumptions.

---

# Scenario 20

## Describe a production-ready Kubernetes deployment for a backend API.

### Answer

A production deployment should include:

- Deployment
- Multiple replicas
- Rolling Updates
- Readiness Probe
- Liveness Probe
- Resource Requests
- Resource Limits
- HPA
- ConfigMaps
- Secrets
- Ingress
- Persistent storage (if required)
- Monitoring
- Logging

This configuration ensures scalability, reliability, security, and maintainability.

---

# Common Mistakes

- Jumping directly to conclusions without checking logs and events.
- Restarting Pods before identifying the root cause.
- Ignoring Service selectors.
- Forgetting Resource Requests and Limits.
- Not mentioning Readiness and Liveness Probes.
- Suggesting manual fixes instead of Kubernetes-native solutions.

---

# Interview Tips

- Explain your troubleshooting process before proposing a solution.
- Mention the `kubectl` commands you would use.
- Think in terms of Kubernetes resources and their relationships.
- Demonstrate a structured debugging methodology.
- Focus on identifying the root cause rather than applying quick fixes.

---

## Key Takeaways

- Scenario-based questions evaluate practical Kubernetes knowledge and problem-solving skills.
- A structured troubleshooting approach is often more important than memorizing commands.
- Understanding how Pods, Deployments, Services, Ingress, storage, and autoscaling work together is essential for resolving production issues.
- Production-ready Kubernetes deployments should emphasize reliability, scalability, observability, and security.
- Demonstrating a logical, methodical approach during interviews leaves a stronger impression than simply listing possible causes.