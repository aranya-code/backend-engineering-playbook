# Storage, ConfigMaps & Secrets

## Overview

Applications often require persistent data and external configuration. Kubernetes provides **Persistent Volumes (PV)**, **Persistent Volume Claims (PVC)**, **ConfigMaps**, and **Secrets** to separate application code from data and configuration.

Understanding these resources is essential for building production-ready Kubernetes applications and is a common topic in technical interviews.

---

# Why These Questions Matter

Interviewers ask storage and configuration questions to evaluate your understanding of:

- Persistent storage
- Stateful applications
- Configuration management
- Secret management
- Security best practices
- Production deployments

---

# Beginner Questions

## 1. Why can't Pods store persistent data?

**Answer**

Pods are **ephemeral**.

When a Pod is deleted or recreated, its local filesystem is also deleted.

Any important data stored inside the Pod is lost.

---

## 2. What is a Volume?

**Answer**

A Volume is storage attached to a Pod.

It allows one or more containers inside the Pod to share data.

Some volumes are temporary, while others are persistent.

---

## 3. What is a Persistent Volume (PV)?

**Answer**

A Persistent Volume (PV) is a storage resource managed by Kubernetes.

It exists independently of Pods and provides long-term storage.

Examples include:

- AWS EBS
- Azure Disk
- Google Persistent Disk
- NFS
- Local storage

---

## 4. What is a Persistent Volume Claim (PVC)?

**Answer**

A Persistent Volume Claim (PVC) is a request for storage made by a Pod.

Instead of directly using a PV, applications request storage through a PVC.

Example:

```text
Pod

↓

PVC

↓

Persistent Volume
```

---

## 5. Why do we use PVCs instead of directly using PVs?

**Answer**

PVCs decouple applications from the underlying storage.

Benefits include:

- Portability
- Easier storage management
- Dynamic provisioning
- Better abstraction

---

## 6. What is a StorageClass?

**Answer**

A StorageClass defines how Persistent Volumes are dynamically created.

Instead of manually creating PVs, Kubernetes automatically provisions storage based on the StorageClass.

---

## 7. What is a ConfigMap?

**Answer**

A ConfigMap stores non-sensitive configuration data.

Examples include:

- Environment variables
- Application settings
- URLs
- Feature flags

This keeps configuration separate from application code.

---

## 8. What is a Secret?

**Answer**

A Secret stores sensitive information.

Examples:

- Passwords
- API Keys
- Database credentials
- TLS Certificates
- OAuth tokens

Secrets help avoid hardcoding sensitive data inside applications.

---

## Intermediate Questions

## 9. What is the difference between ConfigMap and Secret?

**Answer**

| ConfigMap | Secret |
|------------|---------|
| Stores non-sensitive data | Stores sensitive data |
| Plain text configuration | Encoded data (Base64) |
| Environment variables | Passwords, tokens, certificates |

---

## 10. Is a Kubernetes Secret encrypted?

**Answer**

Not by default.

Secrets are Base64 encoded, which is **not encryption**.

For production:

- Enable Encryption at Rest.
- Restrict access using RBAC.
- Use external secret management solutions when appropriate.

---

## 11. How can a ConfigMap be used inside a Pod?

**Answer**

ConfigMaps can be mounted as:

- Environment variables
- Configuration files
- Volumes

This allows applications to consume configuration without rebuilding container images.

---

## 12. How can a Secret be used inside a Pod?

**Answer**

Secrets can be mounted as:

- Environment variables
- Files inside a volume

Applications can securely read sensitive values at runtime.

---

## 13. What happens if a PVC cannot find a matching PV?

**Answer**

The PVC remains in the **Pending** state until:

- A suitable PV becomes available, or
- A StorageClass dynamically provisions one.

---

## 14. What is dynamic provisioning?

**Answer**

Dynamic provisioning automatically creates a Persistent Volume when a PVC is created.

This eliminates the need for administrators to manually create PVs.

---

## 15. Which applications require Persistent Volumes?

**Answer**

Examples include:

- PostgreSQL
- MySQL
- MongoDB
- Redis (persistent mode)
- Elasticsearch
- Jenkins

These applications must preserve data beyond the lifecycle of individual Pods.

---

# Advanced Questions

## 16. What is the relationship between PV, PVC, and StorageClass?

**Answer**

```text
Application

↓

Persistent Volume Claim

↓

StorageClass

↓

Persistent Volume

↓

Physical Storage
```

The StorageClass provisions the Persistent Volume, and the Pod uses it through the PVC.

---

## 17. Why should configuration be separated from application code?

**Answer**

Separating configuration:

- Improves portability
- Simplifies deployments
- Supports multiple environments
- Avoids rebuilding container images for configuration changes

---

## 18. Why are Secrets preferred over hardcoding credentials?

**Answer**

Hardcoding credentials:

- Exposes sensitive information
- Makes rotation difficult
- Increases security risks

Secrets centralize credential management and improve security.

---

## 19. Can multiple Pods use the same Persistent Volume?

**Answer**

Yes, depending on the access mode.

Common access modes:

- ReadWriteOnce (RWO)
- ReadOnlyMany (ROX)
- ReadWriteMany (RWX)

Support depends on the underlying storage provider.

---

## 20. What happens if a Pod using a PVC is deleted?

**Answer**

Deleting the Pod does **not** delete the Persistent Volume.

When a new Pod uses the same PVC, it can access the existing data.

---

## 21. What are reclaim policies?

**Answer**

A reclaim policy determines what happens to a Persistent Volume after its PVC is deleted.

Common policies:

- Retain
- Delete
- Recycle (deprecated)

---

## 22. Why are StatefulSets commonly used with Persistent Volumes?

**Answer**

StatefulSets provide:

- Stable Pod identities
- Stable network identities
- Stable persistent storage

This makes them ideal for stateful applications.

---

## 23. What security best practices should be followed for Secrets?

**Answer**

- Enable Encryption at Rest.
- Restrict access with RBAC.
- Rotate credentials regularly.
- Avoid storing secrets in Git repositories.
- Use external secret managers when appropriate.

---

## 24. Can ConfigMaps be updated without rebuilding an image?

**Answer**

Yes.

Configuration can be updated independently of the application image, making deployments more flexible.

---

## 25. When would you choose ConfigMap over Secret?

**Answer**

Use a ConfigMap for non-sensitive configuration such as:

- Application settings
- Logging levels
- URLs
- Feature flags

Use a Secret for passwords, tokens, certificates, and other confidential information.

---

# Common Mistakes

- Storing passwords in ConfigMaps.
- Assuming Base64 encoding is encryption.
- Saving application data inside Pods.
- Forgetting to configure persistent storage for databases.
- Hardcoding credentials into container images.

---

# Interview Tips

- Remember that Pods are ephemeral; Persistent Volumes are not.
- Clearly distinguish between PV and PVC.
- Explain that PVCs request storage, while PVs provide it.
- Mention StorageClasses when discussing dynamic provisioning.
- Highlight that ConfigMaps are for configuration, while Secrets are for sensitive data.
- Discuss security best practices when talking about Secrets.

---

## Key Takeaways

- Persistent Volumes provide durable storage independent of Pod lifecycles.
- Persistent Volume Claims allow applications to request storage without depending on specific storage implementations.
- StorageClasses enable automatic and dynamic storage provisioning.
- ConfigMaps store non-sensitive configuration, while Secrets securely manage sensitive information.
- Proper storage and configuration management are essential for building reliable, secure, and production-ready Kubernetes applications.