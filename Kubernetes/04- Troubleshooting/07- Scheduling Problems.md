# Scheduling Problems

## Overview

The Kubernetes Scheduler is responsible for deciding which Worker Node should run a Pod. Before a Pod starts, the Scheduler evaluates available resources, scheduling constraints, affinity rules, taints, tolerations, storage requirements, and other policies.

When the Scheduler cannot find a suitable node, Pods remain in the **Pending** state and applications may become unavailable.

This guide covers the most common scheduling issues, how to diagnose them, and practical solutions for resolving them.

---

# Why Scheduling Problems Occur

Scheduling failures are commonly caused by:

- Insufficient CPU
- Insufficient Memory
- Node Affinity
- Pod Affinity
- Pod Anti-Affinity
- Taints
- Missing Tolerations
- Persistent Volume constraints
- Node cordoned
- Node NotReady

---

# Pod Stuck in Pending

## Symptoms

```text
STATUS

Pending
```

---

## Possible Causes

- No available Worker Node
- Insufficient resources
- Scheduling rules not satisfied

---

## Investigation

```bash
kubectl describe pod <pod-name>

kubectl get events
```

---

## Resolution

- Check Scheduler events.
- Verify cluster capacity.
- Review affinity rules.
- Verify taints.
- Check storage requirements.

---

# Insufficient CPU

## Symptoms

Events show:

```text
0/5 nodes are available:
Insufficient cpu
```

---

## Possible Causes

- CPU Requests too high
- Cluster capacity exhausted

---

## Investigation

Check node usage:

```bash
kubectl top nodes
```

View Pod resource requests:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

- Reduce CPU Requests.
- Add Worker Nodes.
- Optimize application resource usage.

---

# Insufficient Memory

## Symptoms

```text
0/5 nodes are available:
Insufficient memory
```

---

## Investigation

```bash
kubectl top nodes

kubectl describe pod <pod-name>
```

---

## Resolution

- Reduce memory requests.
- Increase node memory.
- Add additional Worker Nodes.

---

# Node Not Ready

## Symptoms

```text
STATUS

NotReady
```

---

## Investigation

```bash
kubectl get nodes

kubectl describe node <node-name>
```

---

## Resolution

- Restore node connectivity.
- Restart kubelet if necessary.
- Verify networking.
- Check node health.

---

# Node Cordoned

## Symptoms

Pods cannot be scheduled.

Node status:

```text
SchedulingDisabled
```

---

## Investigation

```bash
kubectl get nodes
```

---

## Resolution

Enable scheduling:

```bash
kubectl uncordon <node-name>
```

---

# Node Affinity Mismatch

## Symptoms

Pod remains Pending.

---

## Example

Pod requires:

```yaml
nodeSelector:
  disk: ssd
```

No nodes contain:

```text
disk=ssd
```

---

## Investigation

View labels:

```bash
kubectl get nodes --show-labels
```

Describe Pod:

```bash
kubectl describe pod
```

---

## Resolution

- Add matching node labels.
- Modify Node Affinity.
- Remove unnecessary constraints.

---

# Pod Affinity Problems

## Symptoms

Pod cannot be scheduled near another Pod.

---

## Investigation

```bash
kubectl describe pod
```

Review affinity configuration.

---

## Resolution

- Verify matching labels.
- Review affinity rules.
- Relax scheduling constraints if appropriate.

---

# Pod Anti-Affinity Problems

## Symptoms

Pod remains Pending despite available resources.

---

## Possible Causes

Anti-affinity prevents Pods from sharing nodes.

---

## Investigation

```bash
kubectl describe pod
```

---

## Resolution

- Review Pod Anti-Affinity rules.
- Increase cluster size.
- Modify scheduling requirements.

---

# Missing Tolerations

## Symptoms

Scheduler reports:

```text
Pod didn't tolerate node taint
```

---

## Investigation

View node taints:

```bash
kubectl describe node <node-name>
```

---

## Resolution

Add matching toleration:

```yaml
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "backend"
  effect: "NoSchedule"
```

---

# Tainted Nodes

## Symptoms

Nodes are available but Pods are never scheduled.

---

## Investigation

```bash
kubectl describe node
```

Example:

```text
Taints:

dedicated=backend:NoSchedule
```

---

## Resolution

Either:

- Add tolerations

or

Remove taint:

```bash
kubectl taint nodes node1 dedicated-
```

---

# Persistent Volume Scheduling Issues

## Symptoms

Pod remains Pending.

PVC also Pending.

---

## Investigation

```bash
kubectl get pvc

kubectl describe pvc
```

---

## Resolution

- Bind PVC.
- Verify StorageClass.
- Verify storage availability.

---

# Resource Requests Too High

## Symptoms

Small cluster cannot schedule Pods.

---

## Investigation

Describe Pod:

```bash
kubectl describe pod
```

Review:

```yaml
resources:
  requests:
```

---

## Resolution

Reduce unnecessary Requests.

Example:

```yaml
cpu: 200m

memory: 256Mi
```

instead of:

```yaml
cpu: 4

memory: 8Gi
```

---

# Cluster Autoscaler Not Triggering

## Symptoms

Pending Pods remain Pending.

---

## Investigation

Verify:

- Cluster Autoscaler installed
- Autoscaler logs
- Cloud provider integration

---

## Resolution

- Enable Cluster Autoscaler.
- Verify IAM permissions.
- Review Autoscaler configuration.

---

# Too Many Pods Per Node

## Symptoms

Scheduler reports:

```text
Too many pods
```

---

## Investigation

```bash
kubectl describe node
```

---

## Resolution

- Add Worker Nodes.
- Increase maximum Pod limit if supported.
- Distribute workloads.

---

# Scheduling Troubleshooting Workflow

```text
Pod Pending
      │
      ▼
Describe Pod
      │
      ▼
Review Events
      │
      ▼
Check Node Status
      │
      ▼
Check Resources
      │
      ▼
Review Affinity Rules
      │
      ▼
Review Taints
      │
      ▼
Verify Storage
      │
      ▼
Check Autoscaler
```

---

# Useful Commands

```bash
kubectl get pods

kubectl describe pod <pod-name>

kubectl get events

kubectl get nodes

kubectl describe node <node-name>

kubectl top nodes

kubectl get nodes --show-labels

kubectl get pvc

kubectl describe pvc
```

---

# Best Practices

- Configure realistic Resource Requests.
- Avoid overly restrictive affinity rules.
- Use taints only when necessary.
- Monitor node utilization.
- Enable Cluster Autoscaler in production.
- Regularly review node health.
- Label nodes consistently.

---

# Interview Tips

- A **Pending** Pod usually indicates a scheduling problem, not an application problem.
- Always check **Events** before changing the Deployment.
- Understand the differences between **Node Affinity**, **Pod Affinity**, and **Pod Anti-Affinity**.
- Know how **Taints** and **Tolerations** influence scheduling.
- Resource Requests determine scheduling decisions, while Resource Limits control runtime resource usage.

---

## Key Takeaways

- The Kubernetes Scheduler places Pods on suitable Worker Nodes based on resources and scheduling policies.
- Most scheduling failures result from insufficient resources, affinity rules, taints, storage constraints, or node availability.
- `kubectl describe pod`, `kubectl get events`, and `kubectl describe node` are the primary commands for diagnosing scheduling issues.
- Proper resource planning, consistent node labeling, and well-designed scheduling policies help prevent scheduling failures in production clusters.