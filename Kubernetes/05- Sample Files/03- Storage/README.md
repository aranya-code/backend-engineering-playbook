# Kubernetes Storage Examples

## Overview

The **Storage** folder demonstrates how Kubernetes provides persistent storage for applications using **Persistent Volumes (PV)**, **Persistent Volume Claims (PVC)**, **StorageClasses**, and **StatefulSets**.

Unlike containers, which are ephemeral by nature, persistent storage allows data to survive Pod restarts, rescheduling, upgrades, and failures.

These examples progress from manually provisioned storage to production-ready dynamic provisioning and stateful workloads.

---

# Why This Section Matters

Containers are designed to be disposable.

When a Pod is deleted, its local filesystem is also removed. Applications that store important data—such as databases, uploaded files, or logs—require persistent storage.

Kubernetes solves this problem by separating storage from compute through Persistent Volumes and Persistent Volume Claims.

Understanding these concepts is essential when deploying stateful applications in production.

---


# Navigation

| Step | File | Purpose |
|------|------|---------|
| 01 | **01- Persistent-Volume.yaml** | Learn how Kubernetes represents physical storage. |
| 02 | **02- Persistent-Volume-Claim.yaml** | Learn how applications request persistent storage. |
| 03 | **03- StorageClass.yaml** | Learn dynamic storage provisioning using CSI drivers. |
| 04 | **04- Deployment-With-PVC.yaml** | Mount persistent storage into a Deployment. |
| 05 | **05- StatefulSet-With-PVC.yaml** | Deploy a stateful application with dedicated storage per Pod. |

---

# Learning Path

Study these examples in the following order.

```text
Persistent Volume
        │
        ▼
Persistent Volume Claim
        │
        ▼
StorageClass
        │
        ▼
Deployment + PVC
        │
        ▼
StatefulSet + PVC
```

---

# Storage Architecture

```text
                  Application
                        │
                        ▼
                     Pod
                        │
                        ▼
         Persistent Volume Claim
                        │
                        ▼
              Persistent Volume
                        │
                        ▼
               Physical Storage
```

---

# Dynamic Provisioning Architecture

```text
                Application
                     │
                     ▼
                    Pod
                     │
                     ▼
                   PVC
                     │
                     ▼
              StorageClass
                     │
                     ▼
                CSI Driver
                     │
                     ▼
           Persistent Volume
                     │
                     ▼
             Physical Storage
```

---

# Persistent Volume Lifecycle

```text
Create PV
    │
    ▼
Available
    │
    ▼
PVC Created
    │
    ▼
Bound
    │
    ▼
Mounted by Pod
    │
    ▼
Pod Deleted
    │
    ▼
PVC Still Exists
    │
    ▼
Data Preserved
```

---

# Manual vs Dynamic Provisioning

| Feature | Manual Provisioning | Dynamic Provisioning |
|----------|--------------------|----------------------|
| PV Creation | Administrator | Kubernetes |
| StorageClass Required | No | Yes |
| Scalability | Limited | Excellent |
| Production Ready | Rarely | Yes |
| Common Usage | Learning, Testing | Production |

---

# Stateful vs Stateless Applications

## Stateless Applications

Typically use Deployments.

Examples:

- REST APIs
- Web Servers
- Frontend Applications
- Authentication Services

Storage is usually optional.

---

## Stateful Applications

Require StatefulSets and persistent storage.

Examples:

- PostgreSQL
- MySQL
- MongoDB
- Redis (Persistent Mode)
- Kafka
- Cassandra
- Elasticsearch

Storage is mandatory.

---

# What You'll Learn

After completing this section, you'll understand how to:

- Create Persistent Volumes
- Request storage using PVCs
- Configure StorageClasses
- Mount storage inside Pods
- Build stateful applications
- Understand dynamic storage provisioning
- Deploy databases in Kubernetes

---

# Recommended Workflow

For each example:

1. Read the comments in the YAML file.
2. Deploy the storage resource.
3. Verify the resource status.
4. Inspect the created objects.
5. Deploy the application.
6. Confirm the volume is mounted.
7. Restart or recreate the Pod.
8. Verify that the data persists.

---

# Frequently Used Commands

View Persistent Volumes

```bash
kubectl get pv
```

View Persistent Volume Claims

```bash
kubectl get pvc
```

View StorageClasses

```bash
kubectl get storageclass
```

Short Form

```bash
kubectl get sc
```

Describe a Persistent Volume

```bash
kubectl describe pv <pv-name>
```

Describe a PVC

```bash
kubectl describe pvc <pvc-name>
```

Describe a StorageClass

```bash
kubectl describe storageclass <storageclass-name>
```

View StatefulSets

```bash
kubectl get statefulsets
```

View Mounted Storage

```bash
kubectl exec -it <pod-name> -- df -h
```

---

# Best Practices

- Always use Persistent Volume Claims instead of referencing Persistent Volumes directly.
- Prefer StorageClasses and dynamic provisioning in production.
- Use StatefulSets for databases and other stateful workloads.
- Use Deployments for stateless applications.
- Select the appropriate access mode for your workload.
- Monitor storage usage and capacity regularly.
- Configure regular backups for persistent data.
- Avoid using HostPath volumes outside local development environments.
- Enable storage encryption whenever supported by the underlying storage provider.

---

## Key Takeaways

- Kubernetes separates storage from compute using Persistent Volumes and Persistent Volume Claims.
- Applications interact with Persistent Volume Claims, while Kubernetes manages the underlying Persistent Volumes.
- StorageClasses automate Persistent Volume provisioning and are the preferred approach for production clusters.
- StatefulSets provide stable identities and dedicated storage for stateful applications such as databases and distributed systems.
- Understanding Kubernetes storage is essential for building reliable, production-ready applications that preserve data across Pod lifecycles.