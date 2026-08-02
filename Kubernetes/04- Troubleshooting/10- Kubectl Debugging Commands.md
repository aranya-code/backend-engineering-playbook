# Kubectl Debugging Commands

## Overview

`kubectl` is the primary command-line tool for interacting with Kubernetes clusters. During production incidents, it is the first tool engineers use to inspect resources, collect logs, monitor workloads, and diagnose failures.

Rather than memorizing every available command, it is more useful to understand which commands to use for different troubleshooting scenarios. This guide organizes the most commonly used debugging commands by purpose, making them easy to reference during real-world incidents.

---

# Why These Commands Matter

Most Kubernetes production incidents can be diagnosed using a relatively small set of `kubectl` commands.

These commands help you:

- Inspect cluster resources
- Investigate Pod failures
- Analyze Deployment issues
- Debug networking problems
- Monitor resource usage
- Troubleshoot storage
- Review cluster events

---

# Cluster Information

## View Cluster Information

```bash
kubectl cluster-info
```

Displays:

- Kubernetes API Server
- CoreDNS
- Cluster endpoints

---

## View Kubernetes Version

```bash
kubectl version
```

---

## View Current Context

```bash
kubectl config current-context
```

---

## List All Contexts

```bash
kubectl config get-contexts
```

---

## Switch Context

```bash
kubectl config use-context <context-name>
```

---

# Node Debugging

## List Nodes

```bash
kubectl get nodes
```

---

## List Nodes with Details

```bash
kubectl get nodes -o wide
```

---

## Describe a Node

```bash
kubectl describe node <node-name>
```

Useful for checking:

- Allocated resources
- Conditions
- Taints
- Capacity
- Events

---

## View Node Labels

```bash
kubectl get nodes --show-labels
```

---

## View Node Resource Usage

```bash
kubectl top node
```

---

# Pod Debugging

## List Pods

```bash
kubectl get pods
```

---

## List Pods in All Namespaces

```bash
kubectl get pods -A
```

---

## List Pods with More Details

```bash
kubectl get pods -o wide
```

---

## Describe a Pod

```bash
kubectl describe pod <pod-name>
```

Shows:

- Events
- Resource Requests
- Resource Limits
- Mounted Volumes
- Scheduling information

---

## View Pod Logs

```bash
kubectl logs <pod-name>
```

---

## View Previous Logs

Useful for CrashLoopBackOff:

```bash
kubectl logs <pod-name> --previous
```

---

## View Logs of a Specific Container

```bash
kubectl logs <pod-name> -c <container-name>
```

---

## Execute Commands Inside a Pod

```bash
kubectl exec -it <pod-name> -- sh
```

or

```bash
kubectl exec -it <pod-name> -- bash
```

Useful for:

- DNS testing
- Network testing
- File inspection

---

## Copy Files from a Pod

```bash
kubectl cp <pod-name>:/tmp/log.txt ./log.txt
```

---

# Deployment Debugging

## List Deployments

```bash
kubectl get deployment
```

---

## Describe Deployment

```bash
kubectl describe deployment <deployment-name>
```

---

## Check Rollout Status

```bash
kubectl rollout status deployment <deployment-name>
```

---

## View Rollout History

```bash
kubectl rollout history deployment <deployment-name>
```

---

## Roll Back Deployment

```bash
kubectl rollout undo deployment <deployment-name>
```

---

## Restart Deployment

```bash
kubectl rollout restart deployment <deployment-name>
```

---

# ReplicaSet Debugging

## List ReplicaSets

```bash
kubectl get rs
```

---

## Describe ReplicaSet

```bash
kubectl describe rs <replicaset-name>
```

---

# Service Debugging

## List Services

```bash
kubectl get svc
```

---

## Describe Service

```bash
kubectl describe svc <service-name>
```

---

## View Service Endpoints

```bash
kubectl get endpoints
```

---

# Networking Debugging

## List Ingresses

```bash
kubectl get ingress
```

---

## Describe Ingress

```bash
kubectl describe ingress <ingress-name>
```

---

## Test DNS from a Pod

```bash
kubectl exec -it <pod-name> -- nslookup backend-service
```

---

## Test Network Connectivity

```bash
kubectl exec -it <pod-name> -- wget http://backend-service
```

---

# Storage Debugging

## List Persistent Volumes

```bash
kubectl get pv
```

---

## List Persistent Volume Claims

```bash
kubectl get pvc
```

---

## Describe PVC

```bash
kubectl describe pvc <pvc-name>
```

---

## Describe PV

```bash
kubectl describe pv <pv-name>
```

---

## List StorageClasses

```bash
kubectl get storageclass
```

---

# Resource Monitoring

## View Pod Resource Usage

```bash
kubectl top pod
```

---

## View Node Resource Usage

```bash
kubectl top node
```

---

## View Horizontal Pod Autoscaler

```bash
kubectl get hpa
```

---

## Describe HPA

```bash
kubectl describe hpa
```

---

# Event Debugging

## View Cluster Events

```bash
kubectl get events
```

---

## Sort Events by Time

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

# Namespace Commands

## List Namespaces

```bash
kubectl get ns
```

---

## View Resources in a Namespace

```bash
kubectl get all -n production
```

---

# Secret & ConfigMap Debugging

## List Secrets

```bash
kubectl get secrets
```

---

## Describe Secret

```bash
kubectl describe secret <secret-name>
```

---

## List ConfigMaps

```bash
kubectl get configmap
```

---

## Describe ConfigMap

```bash
kubectl describe configmap <configmap-name>
```

---

# Debugging Cheat Sheet

| Problem | Command |
|----------|---------|
| Pod not starting | `kubectl describe pod` |
| Pod crashing | `kubectl logs` |
| CrashLoopBackOff | `kubectl logs --previous` |
| Deployment stuck | `kubectl rollout status` |
| Service not working | `kubectl describe svc` |
| No Endpoints | `kubectl get endpoints` |
| PVC Pending | `kubectl describe pvc` |
| High CPU | `kubectl top pod` |
| Node issue | `kubectl describe node` |
| Cluster events | `kubectl get events` |

---

# Production Debugging Workflow

```text
User Reports Issue
        │
        ▼
Check Pod Status
        │
        ▼
Describe Pod
        │
        ▼
Review Logs
        │
        ▼
Check Events
        │
        ▼
Verify Deployment
        │
        ▼
Verify Service
        │
        ▼
Check Endpoints
        │
        ▼
Verify Ingress
        │
        ▼
Inspect Storage
        │
        ▼
Review Node Resources
```

---

# Best Practices

- Use `kubectl describe` before making configuration changes.
- Check Events after reviewing Pod status.
- Use `kubectl logs --previous` for restarting containers.
- Monitor CPU and memory with `kubectl top`.
- Verify Endpoints when troubleshooting Services.
- Inspect rollout status before restarting Deployments.
- Use namespaces consistently to avoid debugging the wrong resources.

---

# Interview Tips

- `kubectl describe` is usually the first command to inspect resource details and Events.
- `kubectl logs --previous` is essential for investigating CrashLoopBackOff issues.
- `kubectl get endpoints` quickly identifies whether a Service has healthy backend Pods.
- `kubectl rollout status` and `kubectl rollout undo` are key commands for deployment troubleshooting.
- Organizing commands by troubleshooting workflow demonstrates practical Kubernetes experience in interviews.

---

## Key Takeaways

- A small set of `kubectl` commands can diagnose the majority of Kubernetes production issues.
- Grouping commands by resource type and troubleshooting task makes incident response faster and more systematic.
- Logs, Events, resource descriptions, and rollout status provide the most valuable debugging information.
- Developing a structured debugging workflow is more effective than memorizing isolated commands.