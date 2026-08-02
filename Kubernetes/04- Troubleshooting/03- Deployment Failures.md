# Deployment Failures

## Overview

Deployments are the recommended way to manage stateless applications in Kubernetes. They provide declarative updates, rolling deployments, rollbacks, and self-healing capabilities. However, deployments can still fail due to application errors, configuration mistakes, resource shortages, or failed health checks.

This guide explains the most common Deployment-related issues, how to investigate them, and the steps required to restore a healthy deployment.

---

# Why Deployment Failures Occur

Deployment failures commonly result from:

- Failed rolling updates
- Readiness Probe failures
- Image issues
- Configuration errors
- Insufficient cluster resources
- Failed scheduling
- Application startup failures
- ReplicaSet issues

Understanding these problems helps minimize production downtime and enables faster incident resolution.

---

# Deployment Not Progressing

## Symptoms

```text
deployment "backend-api" exceeded its progress deadline
```

or

```text
ProgressDeadlineExceeded
```

---

## Possible Causes

- Pods failing to start
- Readiness Probe failures
- Image pull failures
- Application crashes
- Resource shortages

---

## Investigation

Check deployment status:

```bash
kubectl rollout status deployment backend-api
```

Describe deployment:

```bash
kubectl describe deployment backend-api
```

View Pods:

```bash
kubectl get pods
```

---

## Resolution

- Check Pod logs.
- Verify probes.
- Verify image.
- Verify resources.
- Roll back if necessary.

---

# Rolling Update Stuck

## Symptoms

Deployment remains in:

```text
Updating...
```

for an unusually long time.

---

## Possible Causes

- Readiness Probe never succeeds
- New Pods crash
- Old Pods cannot terminate
- maxUnavailable too restrictive

---

## Investigation

```bash
kubectl rollout status deployment backend-api

kubectl get rs

kubectl get pods
```

---

## Resolution

- Fix Readiness Probe.
- Verify application startup.
- Review rollout strategy.
- Roll back deployment if necessary.

---

# Replica Count Incorrect

## Symptoms

Desired replicas:

```text
5
```

Current:

```text
3
```

---

## Possible Causes

- Pending Pods
- Failed Pods
- Scheduling problems
- Insufficient cluster resources

---

## Investigation

```bash
kubectl get deployment

kubectl get rs

kubectl get pods
```

---

## Resolution

- Check Pending Pods.
- Verify cluster capacity.
- Review Scheduler events.
- Add Worker Nodes if required.

---

# New Pods Never Become Ready

## Symptoms

```text
READY

0/1
```

Pods remain running but never receive traffic.

---

## Possible Causes

- Readiness Probe failure
- Application startup failure
- Database unavailable
- Incorrect configuration

---

## Investigation

```bash
kubectl describe pod <pod-name>

kubectl logs <pod-name>
```

---

## Resolution

- Fix application startup.
- Verify dependent services.
- Correct Readiness Probe.

---

# Deployment Rollout Failed

## Symptoms

Deployment never reaches completion.

---

## Possible Causes

- Invalid container image
- Failed configuration
- Missing Secret
- Missing ConfigMap
- Resource exhaustion

---

## Investigation

```bash
kubectl rollout status deployment backend-api

kubectl describe deployment backend-api

kubectl get events
```

---

## Resolution

- Fix application configuration.
- Verify image.
- Verify ConfigMaps and Secrets.
- Retry deployment.

---

# Deployment Rollback Required

## Symptoms

New version introduces production issues.

---

## Investigation

View rollout history:

```bash
kubectl rollout history deployment backend-api
```

---

## Resolution

Rollback:

```bash
kubectl rollout undo deployment backend-api
```

Rollback to a specific revision:

```bash
kubectl rollout undo deployment backend-api --to-revision=2
```

---

# Deployment Cannot Pull Image

## Symptoms

Pods show:

```text
ImagePullBackOff
```

---

## Possible Causes

- Wrong image tag
- Registry unavailable
- Authentication failure
- Missing imagePullSecret

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Verify image name.
- Verify registry credentials.
- Configure imagePullSecrets.
- Push the missing image.

---

# Deployment Creates CrashLoopBackOff Pods

## Symptoms

Pods continuously restart.

---

## Possible Causes

- Application crash
- Invalid configuration
- Database unavailable
- Missing environment variables

---

## Investigation

```bash
kubectl logs <pod-name>

kubectl logs <pod-name> --previous
```

---

## Resolution

- Fix application errors.
- Verify Secrets.
- Verify ConfigMaps.
- Test locally before redeployment.

---

# Deployment Uses Too Much CPU

## Symptoms

Pods are throttled.

Application becomes slow.

---

## Investigation

```bash
kubectl top pod

kubectl describe pod
```

---

## Resolution

- Increase CPU limits.
- Optimize application.
- Configure HPA.

---

# Deployment Uses Too Much Memory

## Symptoms

```text
OOMKilled
```

---

## Investigation

```bash
kubectl top pod

kubectl describe pod
```

---

## Resolution

- Increase memory limits.
- Optimize memory usage.
- Investigate memory leaks.

---

# Old Pods Never Terminate

## Symptoms

Old Pods remain during a Rolling Update.

---

## Possible Causes

- Long shutdown process
- Finalizers
- Application ignores SIGTERM

---

## Investigation

```bash
kubectl describe pod
```

---

## Resolution

- Handle SIGTERM correctly.
- Reduce shutdown time.
- Review terminationGracePeriodSeconds.

---

# Deployment Troubleshooting Workflow

```text
Check Deployment Status
          │
          ▼
Check ReplicaSets
          │
          ▼
Inspect Pods
          │
          ▼
Review Events
          │
          ▼
View Logs
          │
          ▼
Verify Probes
          │
          ▼
Check Resources
          │
          ▼
Rollback if Required
```

---

# Useful Commands

```bash
kubectl get deployment

kubectl describe deployment <deployment-name>

kubectl rollout status deployment <deployment-name>

kubectl rollout history deployment <deployment-name>

kubectl rollout undo deployment <deployment-name>

kubectl get rs

kubectl get pods

kubectl logs <pod-name>

kubectl get events
```

---

# Best Practices

- Always deploy using Deployments instead of standalone Pods.
- Configure Readiness and Liveness Probes.
- Use Rolling Updates.
- Configure Resource Requests and Limits.
- Monitor deployments after every release.
- Keep rollback history.
- Test deployments in staging before production.

---

# Interview Tips

- A Deployment manages ReplicaSets, not Pods directly.
- Always check the rollout status before troubleshooting Pods.
- Mention `kubectl rollout status` and `kubectl rollout undo` during deployment-related questions.
- Readiness Probe failures are one of the most common reasons for failed deployments.
- Rolling Updates provide zero or minimal downtime and are the default deployment strategy.

---

## Key Takeaways

- Deployment failures are commonly caused by application crashes, failed health checks, configuration issues, or insufficient resources.
- `kubectl rollout`, `kubectl describe`, and `kubectl logs` are the primary tools for diagnosing deployment problems.
- Understanding the relationship between Deployments, ReplicaSets, and Pods is essential for effective troubleshooting.
- A structured troubleshooting process and the ability to perform safe rollbacks are critical skills for managing production Kubernetes deployments.