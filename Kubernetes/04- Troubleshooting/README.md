# Kubernetes Troubleshooting

## Overview

Troubleshooting Kubernetes effectively requires more than knowing individual commands—it requires following a structured process to identify the root cause of production issues.

This section provides a practical troubleshooting guide covering the most common Kubernetes failures, including Pod issues, deployment failures, networking problems, storage errors, scheduling issues, image pull failures, resource bottlenecks, and production debugging workflows.

The notes are designed to help you quickly diagnose and resolve problems in real-world Kubernetes clusters while also preparing you for troubleshooting-focused interview questions.

---

# Why This Section Matters

Production Kubernetes environments are complex.

A single application request passes through multiple components:

- Cluster
- Nodes
- Deployments
- ReplicaSets
- Pods
- Services
- Endpoints
- Ingress
- Storage
- Networking

A failure in any layer can make the application unavailable.

This section teaches a systematic approach to identifying failures instead of relying on trial and error.

---

# Topics Covered

This troubleshooting guide covers:

- Common Kubernetes errors
- Pod troubleshooting
- Deployment failures
- Service and networking issues
- Storage problems
- Image pull failures
- Scheduling issues
- Resource and performance problems
- Ingress troubleshooting
- kubectl debugging commands
- Production troubleshooting workflow
- Troubleshooting decision flowcharts

---

# Navigation

| Step | Topic | Description |
|------|-------|-------------|
| 01 | [Common Kubernetes Errors](01-%20Common%20Kubernetes%20Errors.md) | Learn the meaning of common Kubernetes error states and their root causes. |
| 02 | [Pod Issues](02-%20Pod%20Issues.md) | Diagnose Pod lifecycle problems, restarts, and probe failures. |
| 03 | [Deployment Failures](03-%20Deployment%20Failures.md) | Troubleshoot rollouts, ReplicaSets, and deployment failures. |
| 04 | [Service & Networking Issues](04-%20Service%20&%20Networking%20Issues.md) | Debug Services, DNS, Endpoints, and networking issues. |
| 05 | [Storage Issues](05-%20Storage%20Issues.md) | Resolve Persistent Volume, PVC, and StorageClass problems. |
| 06 | [Image Pull Problems](06-%20Image%20Pull%20Problems.md) | Investigate container image download failures and registry authentication issues. |
| 07 | [Scheduling Problems](07-%20Scheduling%20Problems.md) | Diagnose Pending Pods, resource shortages, and scheduling constraints. |
| 08 | [Resource & Performance Issues](08-%20Resource%20&%20Performance%20Issues.md) | Analyze CPU, memory, autoscaling, and cluster performance. |
| 09 | [Ingress Troubleshooting](09-%20Ingress%20Troubleshooting.md) | Debug external traffic routing, TLS, and Ingress Controller issues. |
| 10 | [kubectl Debugging Commands](10-%20kubectl%20Debugging%20Commands.md) | Reference the most important kubectl commands for debugging Kubernetes clusters. |
| 11 | [Production Troubleshooting Checklist](11-%20Production%20Troubleshooting%20Checklist.md) | Follow a structured checklist for production incident response. |
| 12 | [Troubleshooting Flowcharts](12-%20Troubleshooting%20Flowcharts.md) | Use visual decision trees to isolate and resolve Kubernetes problems efficiently. |

---

# Learning Path

Study the troubleshooting topics in the following order:

```text
Common Kubernetes Errors
            │
            ▼
Pod Issues
            │
            ▼
Deployment Failures
            │
            ▼
Service & Networking Issues
            │
            ▼
Storage Issues
            │
            ▼
Image Pull Problems
            │
            ▼
Scheduling Problems
            │
            ▼
Resource & Performance Issues
            │
            ▼
Ingress Troubleshooting
            │
            ▼
kubectl Debugging Commands
            │
            ▼
Production Troubleshooting Checklist
            │
            ▼
Troubleshooting Flowcharts
```

---

# Files in This Folder

| File | Description |
|------|-------------|
| **01- Common Kubernetes Errors.md** | Explains the most common Kubernetes error states such as CrashLoopBackOff, Pending, OOMKilled, ErrImagePull, and ImagePullBackOff. |
| **02- Pod Issues.md** | Troubleshoot Pod startup failures, health probes, restarts, Pending Pods, and Pod lifecycle issues. |
| **03- Deployment Failures.md** | Diagnose rollout failures, ReplicaSet issues, deployment rollbacks, and failed application updates. |
| **04- Service & Networking Issues.md** | Resolve Service connectivity problems, DNS failures, Endpoints, targetPort mismatches, and networking issues. |
| **05- Storage Issues.md** | Troubleshoot Persistent Volumes, Persistent Volume Claims, StorageClasses, and volume mount failures. |
| **06- Image Pull Problems.md** | Diagnose ErrImagePull, ImagePullBackOff, registry authentication issues, image tags, and private registries. |
| **07- Scheduling Problems.md** | Resolve Pending Pods caused by insufficient resources, affinity rules, taints, tolerations, and scheduling constraints. |
| **08- Resource & Performance Issues.md** | Investigate CPU throttling, memory issues, OOMKilled containers, HPA, and overall cluster performance. |
| **09- Ingress Troubleshooting.md** | Debug HTTP 404, 502, 503, TLS issues, DNS problems, and Ingress Controller configuration. |
| **10- kubectl Debugging Commands.md** | Practical reference for the most useful kubectl commands used during production troubleshooting. |
| **11- Production Troubleshooting Checklist.md** | Step-by-step checklist for diagnosing and recovering from production incidents. |
| **12- Troubleshooting Flowcharts.md** | Visual troubleshooting workflows and decision trees for common Kubernetes failures. |

---

# Quick Navigation

| Category | Description |
|----------|-------------|
| **Pod Issues** | Diagnose application startup failures and container problems. |
| **Deployments** | Troubleshoot rollouts, ReplicaSets, and release failures. |
| **Networking** | Debug Services, Endpoints, DNS, and Ingress routing. |
| **Storage** | Resolve PV, PVC, StorageClass, and volume mount issues. |
| **Scheduling** | Investigate Pending Pods, affinity rules, taints, and node resources. |
| **Performance** | Analyze CPU, memory, autoscaling, and resource bottlenecks. |
| **Production Operations** | Follow incident response checklists and debugging workflows. |

---

# Recommended Troubleshooting Workflow

Whenever an issue occurs, follow this sequence:

```text
Incident Reported
        │
        ▼
Check Cluster Health
        │
        ▼
Check Nodes
        │
        ▼
Check Deployments
        │
        ▼
Check ReplicaSets
        │
        ▼
Check Pods
        │
        ▼
Review Events
        │
        ▼
Review Logs
        │
        ▼
Verify Resources
        │
        ▼
Verify Services
        │
        ▼
Check Endpoints
        │
        ▼
Check Ingress
        │
        ▼
Verify Storage
        │
        ▼
Identify Root Cause
        │
        ▼
Apply Fix
        │
        ▼
Verify Recovery
```

---

# Production Troubleshooting Principles

When debugging Kubernetes in production:

- Investigate before making changes.
- Check Events before restarting Pods.
- Review logs before changing configurations.
- Identify the root cause rather than treating symptoms.
- Validate the fix before closing the incident.
- Document recurring issues for future reference.

---

## Key Takeaways

- Kubernetes troubleshooting is most effective when performed using a structured, repeatable workflow.
- Most production incidents originate from Pods, Deployments, Services, networking, storage, scheduling, or resource constraints.
- Logs, Events, resource descriptions, and rollout status provide the most valuable diagnostic information.
- Following systematic troubleshooting procedures reduces downtime, improves reliability, and builds confidence when managing Kubernetes in production.