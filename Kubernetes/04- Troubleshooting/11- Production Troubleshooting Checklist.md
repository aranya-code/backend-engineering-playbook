# Production Troubleshooting Checklist

## Overview

Production incidents require a structured and disciplined approach. Randomly restarting Pods or changing configurations without understanding the root cause can make an outage worse.

This guide provides a step-by-step production troubleshooting checklist that can be followed during Kubernetes incidents. It is designed to help engineers quickly isolate issues, minimize downtime, and restore application availability.

---

# Why This Checklist Matters

During production incidents:

- Every minute of downtime matters.
- Random changes increase risk.
- Logs may disappear after restarts.
- Multiple components may be affected simultaneously.

Following a consistent troubleshooting process ensures that no critical checks are missed.

---

# Golden Rule

> **Never make changes before understanding the problem.**

Always investigate first.

---

# Step 1 - Identify the Problem

Ask:

- What is failing?
- Is the issue affecting all users?
- Is it intermittent?
- When did it start?
- Was a deployment recently completed?

Collect information before making changes.

---

# Step 2 - Check Cluster Health

Verify cluster status.

```bash
kubectl get nodes
```

Healthy output:

```text
NAME          STATUS

worker-1      Ready

worker-2      Ready
```

If nodes are **NotReady**, investigate node health first.

---

# Step 3 - Check Namespace

Verify you're troubleshooting the correct environment.

```bash
kubectl get ns
```

List resources:

```bash
kubectl get all -n production
```

---

# Step 4 - Check Deployments

Verify deployment status.

```bash
kubectl get deployment
```

Describe deployment.

```bash
kubectl describe deployment backend-api
```

Check rollout.

```bash
kubectl rollout status deployment backend-api
```

---

# Step 5 - Check ReplicaSets

```bash
kubectl get rs
```

Verify:

- Desired replicas
- Current replicas
- Available replicas

---

# Step 6 - Check Pods

List Pods.

```bash
kubectl get pods
```

Look for:

- Pending
- CrashLoopBackOff
- ImagePullBackOff
- Error
- OOMKilled
- Terminating

---

# Step 7 - Describe the Pod

```bash
kubectl describe pod <pod-name>
```

Pay attention to:

- Events
- Scheduling
- Mounted volumes
- Resource limits
- Health probes

Events often reveal the root cause.

---

# Step 8 - Review Logs

Current logs:

```bash
kubectl logs <pod-name>
```

Previous logs:

```bash
kubectl logs <pod-name> --previous
```

Look for:

- Exceptions
- Database errors
- Authentication failures
- Missing configuration
- Startup failures

---

# Step 9 - Verify Resource Usage

Pod usage:

```bash
kubectl top pod
```

Node usage:

```bash
kubectl top node
```

Check for:

- High CPU
- High Memory
- Resource exhaustion

---

# Step 10 - Verify Services

```bash
kubectl get svc
```

Describe Service.

```bash
kubectl describe svc backend-service
```

Verify:

- Service type
- Selector
- Ports

---

# Step 11 - Verify Endpoints

```bash
kubectl get endpoints
```

Expected:

```text
backend-service

10.1.1.20

10.1.1.25
```

If:

```text
<none>
```

then check:

- Labels
- Selectors
- Readiness Probe

---

# Step 12 - Verify Networking

Check Ingress.

```bash
kubectl get ingress
```

Describe Ingress.

```bash
kubectl describe ingress
```

Verify:

- Host
- Path
- Backend Service

---

# Step 13 - Verify DNS

Enter a Pod.

```bash
kubectl exec -it <pod-name> -- sh
```

Test DNS.

```bash
nslookup backend-service
```

Test connectivity.

```bash
wget backend-service
```

---

# Step 14 - Verify Storage

List PVCs.

```bash
kubectl get pvc
```

Describe PVC.

```bash
kubectl describe pvc
```

Verify:

- Bound status
- StorageClass
- Capacity

---

# Step 15 - Review Events

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

Common issues include:

- FailedScheduling
- FailedMount
- FailedAttachVolume
- FailedPullImage
- Probe failures

---

# Step 16 - Verify Recent Changes

Ask:

- Was a new Deployment released?
- Were ConfigMaps updated?
- Were Secrets modified?
- Was infrastructure changed?

Check rollout history.

```bash
kubectl rollout history deployment backend-api
```

---

# Step 17 - Roll Back if Necessary

If the issue started immediately after deployment:

```bash
kubectl rollout undo deployment backend-api
```

Confirm:

```bash
kubectl rollout status deployment backend-api
```

---

# Step 18 - Verify Recovery

Confirm:

- Pods are Ready.
- Services have Endpoints.
- Application responds.
- CPU usage is normal.
- Memory usage is stable.
- Users can access the application.

---

# Production Incident Flow

```text
Incident Reported
        │
        ▼
Check Cluster
        │
        ▼
Check Deployment
        │
        ▼
Check ReplicaSet
        │
        ▼
Check Pods
        │
        ▼
Describe Pod
        │
        ▼
Review Logs
        │
        ▼
Review Events
        │
        ▼
Check Resources
        │
        ▼
Check Service
        │
        ▼
Check Endpoints
        │
        ▼
Check Ingress
        │
        ▼
Check Storage
        │
        ▼
Rollback if Required
        │
        ▼
Verify Recovery
```

---

# Quick Production Checklist

| Check | Completed |
|--------|-----------|
| Cluster Healthy | ☐ |
| Nodes Ready | ☐ |
| Deployment Healthy | ☐ |
| ReplicaSets Healthy | ☐ |
| Pods Running | ☐ |
| Pod Logs Reviewed | ☐ |
| Events Reviewed | ☐ |
| Services Verified | ☐ |
| Endpoints Verified | ☐ |
| Ingress Verified | ☐ |
| DNS Working | ☐ |
| Storage Healthy | ☐ |
| Resources Normal | ☐ |
| Recent Changes Reviewed | ☐ |
| Rollback Considered | ☐ |
| Recovery Verified | ☐ |

---

# Best Practices

- Never restart Pods before collecting logs.
- Review Events before changing configurations.
- Investigate root causes instead of symptoms.
- Document every production incident.
- Automate monitoring and alerting.
- Perform post-incident reviews.
- Keep rollback procedures tested and documented.

---

# Interview Tips

- Explain a **structured troubleshooting methodology** instead of jumping to conclusions.
- Mention checking **Events**, **Logs**, **Services**, and **Endpoints** before making changes.
- Discuss rollback as a controlled recovery strategy, not the first action.
- Emphasize root cause analysis and post-incident learning.

---

## Key Takeaways

- A consistent troubleshooting checklist reduces downtime and improves incident response.
- Production debugging should follow a logical sequence from cluster health to application-level diagnostics.
- Logs, Events, resource utilization, networking, and storage should all be verified before implementing fixes.
- Successful production support requires not only restoring service but also identifying and preventing the root cause of future incidents.