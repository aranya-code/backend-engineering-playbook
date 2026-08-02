# Storage Issues

## Overview

Persistent storage is essential for stateful applications such as databases, message queues, search engines, and file storage systems. Kubernetes uses **Persistent Volumes (PV)**, **Persistent Volume Claims (PVC)**, and **StorageClasses** to provide durable storage.

When storage is misconfigured, Pods may remain in the **Pending** state, fail to start, or lose access to persistent data. This guide explains the most common storage-related issues, how to diagnose them, and how to resolve them.

---

# Why Storage Issues Occur

Storage-related problems usually occur because of:

- Missing Persistent Volumes
- Incorrect StorageClasses
- PVC binding failures
- Access mode mismatches
- Volume mount failures
- Cloud storage issues
- Permission problems

---

# PVC Stuck in Pending

## Symptoms

```text
STATUS

Pending
```

The Persistent Volume Claim cannot bind to a Persistent Volume.

---

## Possible Causes

- No available Persistent Volume
- Incorrect StorageClass
- Capacity mismatch
- Access mode mismatch

---

## Investigation

Check PVC:

```bash
kubectl get pvc
```

Describe PVC:

```bash
kubectl describe pvc <pvc-name>
```

Check available PVs:

```bash
kubectl get pv
```

---

## Resolution

- Create a matching Persistent Volume.
- Verify StorageClass.
- Verify requested capacity.
- Verify access mode.

---

# Pod Cannot Mount Volume

## Symptoms

```text
FailedMount
```

or

```text
Unable to attach or mount volumes
```

---

## Possible Causes

- PVC not bound
- Missing PV
- Storage backend unavailable
- Wrong StorageClass

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Check PVC:

```bash
kubectl get pvc
```

---

## Resolution

- Verify PVC status.
- Verify PV binding.
- Check StorageClass.
- Verify cloud storage availability.

---

# Persistent Volume Not Bound

## Symptoms

```text
STATUS

Available
```

The PV exists but is not being used.

---

## Possible Causes

- Capacity mismatch
- Access mode mismatch
- Different StorageClass
- PVC selector mismatch

---

## Investigation

```bash
kubectl describe pv <pv-name>

kubectl describe pvc <pvc-name>
```

---

## Resolution

Ensure both resources have matching:

- StorageClass
- Capacity
- Access Mode

---

# StorageClass Not Found

## Symptoms

```text
storageclass.storage.k8s.io not found
```

---

## Investigation

List StorageClasses:

```bash
kubectl get storageclass
```

---

## Resolution

- Create the missing StorageClass.
- Update the PVC to use an existing StorageClass.

---

# Dynamic Provisioning Not Working

## Symptoms

PVC remains Pending even though a StorageClass exists.

---

## Possible Causes

- Storage provisioner unavailable
- Cloud integration issue
- CSI driver missing

---

## Investigation

Check StorageClass:

```bash
kubectl describe storageclass
```

Check CSI Pods:

```bash
kubectl get pods -n kube-system
```

---

## Resolution

- Verify CSI Driver.
- Verify cloud permissions.
- Restart storage provisioner if necessary.

---

# Access Mode Mismatch

## Symptoms

PVC cannot bind.

---

## Example

PVC:

```yaml
accessModes:
- ReadWriteMany
```

PV:

```yaml
accessModes:
- ReadWriteOnce
```

---

## Investigation

```bash
kubectl describe pvc

kubectl describe pv
```

---

## Resolution

Use matching access modes.

Common modes:

- ReadWriteOnce (RWO)
- ReadOnlyMany (ROX)
- ReadWriteMany (RWX)

---

# Volume Mount Failed

## Symptoms

```text
MountVolume.SetUp failed
```

---

## Possible Causes

- Invalid mount path
- Missing PVC
- Storage backend unavailable
- Permission issues

---

## Investigation

```bash
kubectl describe pod
```

Review Events.

---

## Resolution

- Verify mount path.
- Verify PVC.
- Verify storage backend.
- Verify permissions.

---

# Read-Only File System

## Symptoms

Application cannot write files.

Example:

```text
Read-only file system
```

---

## Possible Causes

- Wrong access mode
- Read-only volume mount
- Storage configuration

---

## Investigation

Inspect volume mounts:

```bash
kubectl describe pod
```

---

## Resolution

- Use writable mount.
- Verify access mode.
- Check mount options.

---

# Volume Permission Denied

## Symptoms

```text
Permission denied
```

---

## Possible Causes

- Incorrect file ownership
- Incorrect security context
- Non-root container

---

## Investigation

Enter the Pod:

```bash
kubectl exec -it <pod-name> -- sh
```

Check permissions:

```bash
ls -l
```

---

## Resolution

- Configure `securityContext`.
- Adjust file permissions.
- Set appropriate user and group IDs.

---

# Cloud Storage Not Attaching

## Symptoms

Volumes remain unattached.

---

## Possible Causes

- Cloud API failure
- Missing IAM permissions
- Wrong availability zone
- CSI Driver issue

---

## Investigation

```bash
kubectl describe pvc

kubectl describe pod
```

Review cloud provider logs if available.

---

## Resolution

- Verify IAM permissions.
- Verify storage availability zone.
- Restart CSI components if necessary.

---

# Data Lost After Pod Restart

## Symptoms

Application data disappears.

---

## Possible Causes

- Using emptyDir
- No PVC
- Incorrect volume configuration

---

## Investigation

Inspect Pod specification:

```bash
kubectl describe pod
```

---

## Resolution

Use:

```text
Persistent Volume

↓

Persistent Volume Claim

↓

Pod
```

Avoid storing important data inside the container filesystem.

---

# Storage Troubleshooting Workflow

```text
Storage Issue
      │
      ▼
Check Pod
      │
      ▼
Check PVC
      │
      ▼
Check PV
      │
      ▼
Check StorageClass
      │
      ▼
Check Events
      │
      ▼
Verify Mount
      │
      ▼
Verify Permissions
      │
      ▼
Check Cloud Storage
```

---

# Useful Commands

```bash
kubectl get pvc

kubectl describe pvc <pvc-name>

kubectl get pv

kubectl describe pv <pv-name>

kubectl get storageclass

kubectl describe pod <pod-name>

kubectl get events

kubectl exec -it <pod-name> -- sh
```

---

# Best Practices

- Always use PVCs instead of directly referencing Persistent Volumes.
- Use StorageClasses for dynamic provisioning.
- Match access modes correctly.
- Monitor storage capacity and usage.
- Back up important persistent data regularly.
- Test storage recovery procedures.
- Avoid storing application data inside container filesystems.

---

# Interview Tips

- A PVC in **Pending** usually indicates a binding or provisioning problem.
- A Pod cannot mount a volume until its PVC is successfully bound.
- StorageClasses enable dynamic volume provisioning.
- Know the differences between **PV**, **PVC**, and **StorageClass**.
- Remember the common access modes: **ReadWriteOnce (RWO)**, **ReadOnlyMany (ROX)**, and **ReadWriteMany (RWX)**.

---

## Key Takeaways

- Most Kubernetes storage issues are related to Persistent Volume Claims, StorageClasses, access modes, or volume mounts.
- `kubectl describe pod`, `kubectl describe pvc`, and `kubectl describe pv` are the primary commands for diagnosing storage problems.
- Proper configuration of PVs, PVCs, and StorageClasses ensures reliable persistent storage for stateful applications.
- Understanding Kubernetes storage architecture is essential for running production databases and other stateful workloads reliably.