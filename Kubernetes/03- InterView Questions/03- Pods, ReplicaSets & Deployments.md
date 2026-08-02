# Pods, ReplicaSets & Deployments

## Overview

Pods, ReplicaSets, and Deployments are the core workload resources in Kubernetes. They define how applications are executed, scaled, updated, and maintained within a cluster.

These topics are among the most frequently discussed during Kubernetes interviews because they demonstrate an understanding of how Kubernetes manages application lifecycles and ensures high availability.

---

# Why These Questions Matter

Interviewers ask these questions to assess whether you understand:

- The relationship between Pods, ReplicaSets, and Deployments
- Application lifecycle management
- High availability
- Rolling updates and rollbacks
- Kubernetes self-healing
- Production deployment practices

---

# Beginner Questions

## 1. What is a Pod?

**Answer**

A Pod is the smallest deployable unit in Kubernetes.

A Pod can contain:

- One container (most common)
- Multiple tightly coupled containers

Containers inside a Pod share:

- IP address
- Network namespace
- Storage volumes
- localhost communication

---

## 2. Why are Pods considered ephemeral?

**Answer**

Pods are temporary by design.

If a Pod crashes or is deleted, Kubernetes creates a new Pod instead of repairing the existing one.

Applications should therefore remain stateless whenever possible.

---

## 3. Can multiple containers run inside one Pod?

**Answer**

Yes.

Multiple containers can run inside the same Pod.

Common examples include:

- Application container
- Logging sidecar
- Monitoring agent
- Service mesh proxy

All containers communicate over `localhost`.

---

## 4. What is a ReplicaSet?

**Answer**

A ReplicaSet ensures that a specified number of Pod replicas are always running.

Example:

Desired replicas:

```text
3
```

If one Pod crashes:

```text
2 Running

↓

ReplicaSet creates another Pod

↓

3 Running
```

---

## 5. Why do we need ReplicaSets?

**Answer**

ReplicaSets provide:

- High availability
- Automatic Pod replacement
- Self-healing
- Desired replica management

---

## 6. What is a Deployment?

**Answer**

A Deployment manages ReplicaSets and provides declarative updates for Pods.

It supports:

- Rolling updates
- Rollbacks
- Scaling
- Version management

Deployments are the recommended way to run stateless applications.

---

## 7. What is the relationship between Deployment, ReplicaSet, and Pod?

**Answer**

```text
Deployment

↓

ReplicaSet

↓

Pods
```

A Deployment creates and manages ReplicaSets, and ReplicaSets manage Pods.

---

## 8. Should we create Pods directly in production?

**Answer**

No.

Standalone Pods are typically used only for:

- Testing
- Learning
- Debugging

Production applications should be managed through Deployments.

---

## Intermediate Questions

## 9. What happens if a Pod crashes?

**Answer**

If the Pod belongs to a ReplicaSet or Deployment:

```text
Pod Crashes

↓

ReplicaSet detects missing Pod

↓

Creates a new Pod

↓

Desired state restored
```

This is Kubernetes' self-healing capability.

---

## 10. How does a Deployment perform rolling updates?

**Answer**

A Deployment gradually replaces old Pods with new Pods.

Example:

```text
Version 1

● ● ●

↓

● ● ○

↓

● ○ ○

↓

○ ○ ○

Version 2
```

This minimizes downtime during updates.

---

## 11. What is a rollback?

**Answer**

A rollback restores a previous version of a Deployment if the new version fails.

Command:

```bash
kubectl rollout undo deployment <deployment-name>
```

---

## 12. What is the default Deployment strategy?

**Answer**

**RollingUpdate**

It replaces Pods gradually while keeping the application available.

---

## 13. What is a Replica?

**Answer**

A replica is a running instance of a Pod.

Example:

```yaml
replicas: 5
```

means Kubernetes maintains five identical Pods.

---

## 14. How do you scale a Deployment?

**Answer**

Using kubectl:

```bash
kubectl scale deployment backend-api --replicas=5
```

Or by modifying the Deployment manifest.

---

## 15. What happens if a node hosting Pods fails?

**Answer**

The Control Plane detects the node failure.

ReplicaSets create replacement Pods on healthy Worker Nodes.

---

## Advanced Questions

## 16. Why is a Deployment preferred over a ReplicaSet?

**Answer**

ReplicaSets only maintain replica counts.

Deployments provide additional capabilities:

- Rolling updates
- Rollbacks
- Version history
- Controlled deployments

In practice, users almost always create Deployments instead of ReplicaSets directly.

---

## 17. What happens when you update a Deployment?

**Answer**

Kubernetes creates a new ReplicaSet.

The new ReplicaSet gradually replaces Pods from the old ReplicaSet.

Once the rollout completes, the old ReplicaSet is retained for rollback purposes.

---

## 18. How does Kubernetes achieve self-healing?

**Answer**

Controllers continuously compare the desired state with the actual state.

If a Pod disappears:

```text
Desired:
3 Pods

Actual:
2 Pods

↓

ReplicaSet creates another Pod
```

---

## 19. Can multiple ReplicaSets exist for one Deployment?

**Answer**

Yes.

During rolling updates:

- Old ReplicaSet
- New ReplicaSet

exist simultaneously until the rollout completes.

---

## 20. Why shouldn't applications rely on Pod IP addresses?

**Answer**

Pod IP addresses are temporary.

When a Pod is recreated:

- A new IP address is assigned.

Applications should communicate using Kubernetes Services rather than Pod IPs.

---

## 21. What is the difference between scaling and rolling updates?

**Answer**

Scaling changes the number of replicas.

Example:

```text
3 Pods

↓

6 Pods
```

Rolling updates replace one application version with another while maintaining availability.

---

## 22. What are maxSurge and maxUnavailable?

**Answer**

They control rolling update behavior.

**maxSurge**

Maximum additional Pods created during an update.

**maxUnavailable**

Maximum number of Pods allowed to be unavailable during the rollout.

These settings help achieve zero-downtime deployments.

---

## 23. What is the purpose of Readiness Probes during rolling updates?

**Answer**

A new Pod receives traffic only after it passes the Readiness Probe.

This prevents users from accessing applications that are still starting.

---

## 24. How do you check the rollout status of a Deployment?

**Answer**

```bash
kubectl rollout status deployment <deployment-name>
```

---

## 25. How do you view Deployment history?

**Answer**

```bash
kubectl rollout history deployment <deployment-name>
```

This displays previous revisions available for rollback.

---

# Common Mistakes

- Creating standalone Pods for production applications.
- Confusing Deployments with ReplicaSets.
- Assuming Pods have permanent IP addresses.
- Forgetting that Deployments create ReplicaSets automatically.
- Not configuring Readiness Probes for rolling updates.

---

# Interview Tips

- Remember the hierarchy:

```text
Deployment

↓

ReplicaSet

↓

Pods
```

- Explain why Pods are ephemeral.
- Mention that Deployments provide rolling updates and rollbacks.
- Always recommend Deployments for stateless applications.
- Highlight Kubernetes' self-healing mechanism when discussing ReplicaSets.

---

## Key Takeaways

- Pods are the smallest deployable units in Kubernetes and are designed to be ephemeral.
- ReplicaSets maintain the desired number of Pod replicas and provide self-healing capabilities.
- Deployments manage ReplicaSets and enable rolling updates, rollbacks, and version control.
- Production applications should typically be deployed using Deployments rather than standalone Pods.
- Understanding the relationship between Pods, ReplicaSets, and Deployments is fundamental to designing reliable and scalable Kubernetes workloads.