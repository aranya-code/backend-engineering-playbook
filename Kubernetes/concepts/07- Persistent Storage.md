# Why Do We Need Persistent Storage?

Containers are **ephemeral** (temporary).

When a container is deleted or restarted, everything stored inside its filesystem is lost.

Example

```
Container

↓

Stores Database Files

↓

Container Crashes

↓

New Container Created

↓

❌ Data Lost
```

This is unacceptable for databases and user data.

Kubernetes solves this problem using **Persistent Volumes (PV)**, **Persistent Volume Claims (PVC)**, and **StorageClasses**.

---

# Kubernetes Storage Architecture

```
Application

↓

Pod

↓

Persistent Volume Claim (PVC)

↓

Persistent Volume (PV)

↓

Physical Storage

(AWS EBS / Azure Disk / GCP PD / NFS / SAN)
```

---

# What is a Persistent Volume (PV)?

A **Persistent Volume (PV)** is a storage resource in Kubernetes.

It represents real storage that exists outside the Pod.

Think of it as a hard disk attached to the cluster.

Example storage

- AWS EBS
- Azure Managed Disk
- Google Persistent Disk
- NFS
- Local Disk
- SAN

---

# Characteristics of PV

- Independent of Pods
- Stores persistent data
- Can outlive Pods
- Managed by Kubernetes
- Can be shared (depending on access mode)

---

# Persistent Volume Lifecycle

```
Create PV

↓

Application uses PV

↓

Pod Deleted

↓

PV Still Exists

↓

New Pod can reuse it
```

---

# Persistent Volume Example

```
Kubernetes Cluster

↓

Persistent Volume

↓

100 GB SSD

↓

AWS EBS Volume
```

---

# Persistent Volume Claim (PVC)

Applications do not directly use a Persistent Volume.

Instead, they create a **Persistent Volume Claim (PVC)**.

PVC is a request for storage.

Think of it as requesting a disk from Kubernetes.

Example

```
Application

↓

Request 20 GB Storage

↓

PVC

↓

PV

↓

Physical Disk
```

---

# Why PVC?

Without PVC

Application needs to know

- Storage location
- Storage type
- Cloud provider

With PVC

Application simply requests

```
20 GB

ReadWriteOnce
```

Kubernetes handles everything else.

---

# PVC Workflow

```
Pod

↓

PVC

↓

PV

↓

Storage
```

---

# Persistent Volume vs Persistent Volume Claim

| Persistent Volume | Persistent Volume Claim |
|-------------------|-------------------------|
| Actual storage | Request for storage |
| Created by Admin | Created by Developer |
| Represents physical disk | Represents storage request |
| Supplies storage | Consumes storage |

---

# StorageClass

StorageClass automates storage provisioning.

Instead of creating PVs manually, Kubernetes creates them automatically when a PVC is created.

This is called **Dynamic Provisioning**.

---

Without StorageClass

```
Admin

↓

Creates PV

↓

Developer creates PVC

↓

PVC binds to PV
```

---

With StorageClass

```
Developer creates PVC

↓

StorageClass

↓

Automatically creates PV

↓

Pod uses storage
```

---

# StorageClass Components

A StorageClass defines

- Storage Type
- Provisioner
- Performance
- Reclaim Policy
- Volume Binding Mode

Example

```
Fast SSD

↓

AWS EBS gp3

↓

StorageClass
```

---

# Storage Provisioning

## Static Provisioning

```
Admin

↓

Creates PV

↓

Developer creates PVC

↓

Pod
```

---

## Dynamic Provisioning

```
Developer creates PVC

↓

StorageClass

↓

PV Created Automatically

↓

Pod
```

Dynamic provisioning is preferred in production.

---

# Access Modes

## ReadWriteOnce (RWO)

One node can mount the volume for reading and writing.

Most common mode.

Example

AWS EBS

---

## ReadOnlyMany (ROX)

Multiple nodes can read the volume.

No writing allowed.

---

## ReadWriteMany (RWX)

Multiple nodes can read and write simultaneously.

Example

NFS

Amazon EFS

Azure Files

---

# Reclaim Policy

Determines what happens after a PVC is deleted.

### Delete

Storage is deleted automatically.

Example

```
Delete PVC

↓

Delete PV

↓

Delete Disk
```

---

### Retain

Storage remains.

Administrator decides what to do.

---

### Recycle (Deprecated)

Older mechanism that cleaned the storage before reuse.

---

# Volume Binding

```
Pod

↓

Persistent Volume Claim

↓

Persistent Volume

↓

Cloud Storage
```

---

# Real-World Example

Suppose you deploy PostgreSQL.

```
Deployment

↓

Pod

↓

PVC

↓

PV

↓

AWS EBS

↓

Database Files
```

If the Pod crashes,

```
Old Pod Deleted

↓

New Pod Created

↓

Same PVC

↓

Same PV

↓

Database Still Available
```

No data is lost.

---

# Complete Storage Architecture

```
                    Application

                          │

                         Pod

                          │

            Persistent Volume Claim

                          │

                Persistent Volume

                          │

                StorageClass (Optional)

                          │

               Physical Storage

         AWS EBS / Azure Disk / GCP PD
```

---

# Persistent Volume YAML

```yaml
apiVersion: v1
kind: PersistentVolume

metadata:
  name: app-pv

spec:
  capacity:
    storage: 10Gi

  accessModes:
    - ReadWriteOnce

  hostPath:
    path: "/data"
```

---

# Persistent Volume Claim YAML

```yaml
apiVersion: v1
kind: PersistentVolumeClaim

metadata:
  name: app-pvc

spec:
  accessModes:
    - ReadWriteOnce

  resources:
    requests:
      storage: 5Gi
```

---

# StorageClass YAML

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass

metadata:
  name: fast-storage

provisioner: kubernetes.io/aws-ebs

parameters:
  type: gp3
```

---

# Useful Commands

View Persistent Volumes

```bash
kubectl get pv
```

---

View Persistent Volume Claims

```bash
kubectl get pvc
```

---

View Storage Classes

```bash
kubectl get storageclass
```

---

Describe PV

```bash
kubectl describe pv
```

---

Describe PVC

```bash
kubectl describe pvc
```

---

Describe StorageClass

```bash
kubectl describe storageclass
```

---

# Interview Questions

## What is a Persistent Volume?

A Persistent Volume is a Kubernetes storage resource that exists independently of Pods and provides persistent storage.

---

## What is a Persistent Volume Claim?

A Persistent Volume Claim is a request for storage made by an application.

---

## Why do we need PVC?

PVC abstracts the underlying storage implementation, allowing applications to request storage without knowing the storage details.

---

## What is a StorageClass?

A StorageClass defines how storage should be dynamically provisioned for Persistent Volume Claims.

---

## Difference between PV and PVC?

| PV | PVC |
|----|-----|
| Actual storage | Request for storage |
| Created by administrator | Created by application |
| Supplies storage | Consumes storage |

---

## Static vs Dynamic Provisioning?

| Static | Dynamic |
|---------|---------|
| PV created manually | PV created automatically |
| Administrator required | StorageClass handles provisioning |
| More manual work | Automated |

---

## What happens if a Pod is deleted?

The Pod is deleted, but the Persistent Volume remains (depending on the reclaim policy), so data is preserved and can be reused.

---

# Key Takeaways

- Containers are ephemeral; their local storage is lost when they stop.
- Persistent Volumes (PV) provide durable storage.
- Persistent Volume Claims (PVC) are requests for storage made by applications.
- StorageClasses automate the creation of Persistent Volumes through dynamic provisioning.
- Access modes determine how a volume can be mounted (RWO, ROX, RWX).
- Reclaim policies control what happens to storage after it is no longer in use.
- Persistent storage is essential for stateful applications such as databases and file storage.