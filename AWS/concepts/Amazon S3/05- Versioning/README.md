# Amazon S3 Versioning

The **Versioning** module introduces one of the most important data protection features in Amazon S3. Versioning preserves multiple versions of an object, protecting against accidental deletion, overwrites, and application errors.

Instead of permanently replacing an object during an upload, Amazon S3 assigns a unique **Version ID** to each revision. This enables organizations to restore previous versions, recover deleted data, integrate with Lifecycle Management, and implement robust disaster recovery strategies.

Versioning is considered a production best practice and is commonly enabled for mission-critical buckets storing application data, backups, logs, documents, and media assets.

---

## Module Information

| Property | Value |
|----------|-------|
| Module | 05 |
| Difficulty | 🟡 Intermediate |
| Estimated Reading Time | 60–75 minutes |
| Articles | 5 |
| Hands-on Labs | Covered later in Module 17 |
| Prerequisites | Modules 01–04 |

---

# 📚 Table of Contents

- Overview
- Learning Objectives
- Topics Covered
- File Navigation
- Learning Roadmap
- Versioning Workflow
- Core Concepts
- Best Practices
- Common Mistakes
- Related Modules
- Navigation

---

# Overview

Without Versioning enabled, uploading an object with the same key permanently replaces the previous object.

With Versioning enabled:

- Every upload creates a new version.
- Previous versions remain recoverable.
- Deletes create **Delete Markers** instead of immediately removing data.
- Lifecycle Rules can manage non-current versions automatically.
- Replication can replicate object versions across Regions.

Versioning is one of the simplest and most effective mechanisms for preventing accidental data loss.

This module covers:

- Versioning fundamentals
- Delete Markers
- MFA Delete
- Lifecycle Integration
- Replication Integration

---

# Learning Objectives

After completing this module, you will be able to:

- Explain how Amazon S3 Versioning works.
- Understand Version IDs.
- Recover deleted or overwritten objects.
- Configure Delete Marker behavior.
- Protect buckets using MFA Delete.
- Manage object versions using Lifecycle Rules.
- Understand how Replication works with Versioning.
- Design resilient storage architectures.

---

# Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Introduction](./01-%20Introduction.md) | Learn how Amazon S3 Versioning works and why it is essential for protecting data. |
| 02 | [Delete Markers](./02-%20Delete%20Markers.md) | Understand how deletes behave after Versioning is enabled and how objects can be recovered. |
| 03 | [MFA Delete](./03-%20MFA%20Delete.md) | Protect object versions from accidental or malicious deletion using multi-factor authentication. |
| 04 | [Lifecycle Integration](./04-%20Lifecycle%20Integration.md) | Automatically transition and remove old object versions using Lifecycle Rules. |
| 05 | [Replication Integration](./05-%20Replication%20Integration.md) | Learn how Versioning works with Same-Region and Cross-Region Replication. |

---

# File Navigation

```text
05- Versioning
│
├── 01- Introduction.md
├── 02- Delete Markers.md
├── 03- MFA Delete.md
├── 04- Lifecycle Integration.md
├── 05- Replication Integration.md
│
└── README.md
```

---

# Learning Roadmap

```text
Introduction
      │
      ▼
Delete Markers
      │
      ▼
MFA Delete
      │
      ▼
Lifecycle Integration
      │
      ▼
Replication Integration
```

---

# Versioning Workflow

```text
                 Upload Object
                       │
                       ▼
                 Version ID v1
                       │
              Upload Same Object
                       │
                       ▼
                 Version ID v2
                       │
                 Delete Object
                       │
                       ▼
                Delete Marker
                       │
               Previous Versions
                  Still Exist
```

With Versioning enabled:

- Every upload creates a new Version ID.
- Existing versions are never overwritten.
- Deleting an object creates a Delete Marker.
- Older versions remain recoverable until permanently removed.

---

# Core Concepts

| Concept | Description |
|----------|-------------|
| Versioning | Stores multiple versions of the same object. |
| Version ID | Unique identifier assigned to every object version. |
| Current Version | The latest version returned during normal object requests. |
| Non-current Version | Older version retained after a newer version is uploaded. |
| Delete Marker | Special marker indicating an object has been deleted without removing previous versions. |
| MFA Delete | Additional protection requiring MFA before permanently deleting versions. |
| Lifecycle Integration | Automates management of non-current object versions. |
| Replication Integration | Replicates object versions to another bucket for disaster recovery. |

---

# Best Practices

- Enable Versioning before moving workloads into production.
- Combine Versioning with Lifecycle Rules to manage storage costs.
- Use Cross-Region Replication for critical workloads.
- Enable MFA Delete for highly sensitive buckets.
- Regularly review non-current object storage.
- Test object recovery procedures.
- Monitor replication status after enabling Versioning.

---

# Common Mistakes

- Assuming Versioning is enabled by default.
- Forgetting that Delete Markers do not permanently remove data.
- Ignoring storage costs associated with non-current versions.
- Enabling Versioning without Lifecycle Rules.
- Believing Replication replaces backup strategies.
- Forgetting that MFA Delete can only be configured by the bucket owner and is not supported through the AWS Management Console.

---

# Related Modules

| Module | Purpose |
|----------|---------|
| [Storage Classes](../04-%20Storage%20Classes/README.md) | Optimize storage for versioned objects. |
| [Security](../06-%20Security/README.md) | Protect versioned buckets using IAM and Bucket Policies. |
| [Lifecycle Management](../08-%20Lifecycle%20Management/README.md) | Automate cleanup of old object versions. |
| [Replication](../09-%20Replication/README.md) | Build highly available storage using replicated object versions. |

---

# Navigation

| Previous | Current | Next |
|----------|---------|------|
| Storage Classes | Versioning | Security |

- ⬆️ **Previous Module:** [Storage Classes](../04-%20Storage%20Classes/README.md)
- 🏠 **Parent:** [Amazon S3](../README.md)
- ➡️ **Next Module:** [Security](../06-%20Security/README.md)

---
