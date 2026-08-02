# Troubleshooting Flowcharts

## Overview

When troubleshooting Kubernetes, jumping randomly between commands often wastes valuable time. Experienced engineers follow a structured decision-making process that narrows down the root cause step by step.

This guide provides practical troubleshooting flowcharts that can be followed during production incidents. These flowcharts are based on common Kubernetes failure scenarios and help engineers quickly identify whether an issue is related to scheduling, networking, storage, deployments, or the application itself.

---

# Why Flowcharts Matter

Flowcharts help you:

- Follow a consistent debugging process
- Avoid overlooking important checks
- Reduce production downtime
- Improve incident response
- Prepare for system design and Kubernetes interviews

---

# Flowchart 1 - Application Not Reachable

```text
Application Not Reachable
        │
        ▼
Is the Pod Running?
        │
 ┌──────┴──────┐
 │             │
No            Yes
 │             │
 ▼             ▼
Describe Pod   Check Service
 │             │
 ▼             ▼
Check Events   Service Exists?
 │             │
 ▼             ▼
Fix Pod       No → Create Service
 │
 ▼
Running?
 │
 ▼
Continue
```

---

# Flowchart 2 - Pod Stuck in Pending

```text
Pod Pending
      │
      ▼
Describe Pod
      │
      ▼
Events
      │
      ▼
Insufficient CPU?
      │
 ┌────┴────┐
 │         │
Yes       No
 │         │
 ▼         ▼
Add Nodes  Check Memory
            │
            ▼
      Check Affinity
            │
            ▼
      Check Taints
            │
            ▼
      Check PVC
```

---

# Flowchart 3 - CrashLoopBackOff

```text
CrashLoopBackOff
        │
        ▼
View Logs
        │
        ▼
Application Error?
        │
 ┌──────┴──────┐
 │             │
Yes           No
 │             │
 ▼             ▼
Fix Code     Check ConfigMap
              │
              ▼
          Check Secret
              │
              ▼
       Check Database
              │
              ▼
      Review Liveness Probe
```

---

# Flowchart 4 - ImagePullBackOff

```text
ImagePullBackOff
         │
         ▼
Describe Pod
         │
         ▼
Image Exists?
         │
 ┌──────┴──────┐
 │             │
No            Yes
 │             │
 ▼             ▼
Fix Image     Private Registry?
                │
          ┌─────┴─────┐
          │           │
         Yes         No
          │           │
          ▼           ▼
Configure Secret   Check Registry
```

---

# Flowchart 5 - Service Not Working

```text
Service Not Working
         │
         ▼
Service Exists?
         │
 ┌──────┴──────┐
 │             │
No            Yes
 │             │
 ▼             ▼
Create       Endpoints?
Service        │
          ┌────┴────┐
          │         │
         None      Exists
          │         │
          ▼         ▼
Check Labels  Check targetPort
                │
                ▼
         Check Container Port
```

---

# Flowchart 6 - Ingress Not Working

```text
Ingress Issue
      │
      ▼
Ingress Exists?
      │
 ┌────┴────┐
 │         │
No        Yes
 │         │
 ▼         ▼
Create   Controller Running?
Ingress      │
        ┌────┴────┐
        │         │
       No        Yes
        │         │
        ▼         ▼
Start Controller
              │
              ▼
      Check Backend Service
              │
              ▼
       Check Endpoints
              │
              ▼
          Check DNS
```

---

# Flowchart 7 - PVC Pending

```text
PVC Pending
      │
      ▼
Describe PVC
      │
      ▼
StorageClass Exists?
      │
 ┌────┴────┐
 │         │
No        Yes
 │         │
 ▼         ▼
Create     PV Available?
StorageClass     │
           ┌─────┴─────┐
           │           │
          No          Yes
           │           │
           ▼           ▼
Create PV   Check Access Mode
```

---

# Flowchart 8 - OOMKilled

```text
OOMKilled
     │
     ▼
Check Memory Usage
     │
     ▼
Memory Leak?
     │
 ┌───┴────┐
 │        │
Yes      No
 │        │
 ▼        ▼
Fix Code Increase Limit
      │
      ▼
Monitor Usage
```

---

# Flowchart 9 - High CPU Usage

```text
High CPU
    │
    ▼
Check CPU Usage
    │
    ▼
Single Pod?
    │
 ┌──┴────┐
 │       │
Yes     No
 │       │
 ▼       ▼
Optimize Code
        │
        ▼
Configure HPA
        │
        ▼
Check Database
```

---

# Flowchart 10 - Deployment Failed

```text
Deployment Failed
        │
        ▼
Rollout Status
        │
        ▼
Pods Running?
        │
 ┌──────┴──────┐
 │             │
No            Yes
 │             │
 ▼             ▼
Describe Pod   Ready?
 │             │
 ▼             ▼
View Logs     No
 │             │
 ▼             ▼
Fix Issue   Check Probe
              │
              ▼
       Rollback if Needed
```

---

# Universal Kubernetes Debugging Flow

```text
Incident Reported
        │
        ▼
Cluster Healthy?
        │
        ▼
Nodes Healthy?
        │
        ▼
Deployment Healthy?
        │
        ▼
Pods Running?
        │
        ▼
Events
        │
        ▼
Logs
        │
        ▼
Resources
        │
        ▼
Service
        │
        ▼
Endpoints
        │
        ▼
Ingress
        │
        ▼
Storage
        │
        ▼
Networking
        │
        ▼
Application
        │
        ▼
Root Cause Identified
        │
        ▼
Apply Fix
        │
        ▼
Verify Recovery
```

---

# Production Incident Decision Tree

```text
User Reports Issue
        │
        ▼
Is Everyone Affected?
        │
 ┌──────┴──────┐
 │             │
Yes           No
 │             │
 ▼             ▼
Infrastructure  Single Service
 │               │
 ▼               ▼
Cluster Check    Application Check
 │               │
 ▼               ▼
Resources      Deployment
 │               │
 ▼               ▼
Networking     Logs
 │               │
 ▼               ▼
Storage       Root Cause
```

---

# Best Practices

- Follow the same troubleshooting sequence for every incident.
- Gather evidence before making changes.
- Review Events and Logs before restarting workloads.
- Verify Services, Endpoints, and Ingress before assuming a networking problem.
- Document recurring issues and their resolutions.
- Convert frequently encountered issues into runbooks for your team.

---

# Interview Tips

- Interviewers value a structured troubleshooting process more than memorizing commands.
- Walk through the flowchart verbally when answering scenario-based questions.
- Explain **why** each step is performed before moving to the next.
- Mention the `kubectl` commands you would use at each stage.
- Focus on identifying the **root cause**, not just restoring service.

---

## Key Takeaways

- Flowcharts provide a repeatable approach to Kubernetes troubleshooting and reduce guesswork during incidents.
- Most Kubernetes problems can be isolated by following a logical sequence: Pods → Events → Logs → Resources → Networking → Storage → Application.
- A systematic troubleshooting methodology is a key skill for backend engineers, DevOps engineers, and SREs working with Kubernetes in production.
```