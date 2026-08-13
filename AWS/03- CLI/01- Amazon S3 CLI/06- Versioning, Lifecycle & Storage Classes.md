# Versioning, Lifecycle & Storage Classes

> Learn how Amazon S3 protects data using Versioning, automates object management with Lifecycle Rules, and reduces storage costs using appropriate Storage Classes.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon S3 Versioning.
- Recover deleted or overwritten objects.
- Configure Lifecycle Rules.
- Transition objects between Storage Classes.
- Expire objects automatically.
- Choose the appropriate Storage Class.
- Optimize storage costs.
- Build backup and disaster recovery strategies.

---

# Why This Chapter Matters

Simply uploading objects to S3 is not enough.

Production systems must also address:

- Data protection
- Disaster recovery
- Compliance
- Storage optimization
- Cost management

Amazon S3 provides Versioning, Lifecycle Policies, and Storage Classes to solve these problems.

---

# Understanding S3 Versioning

By default, S3 stores only the latest version of an object.

Without Versioning:

```text
Upload report.pdf

↓

Upload another report.pdf

↓

Previous version is permanently replaced
```

The original object cannot be recovered.

---

# What is Versioning?

Versioning allows Amazon S3 to keep multiple versions of the same object.

Example:

```text
report.pdf

├── Version 1

├── Version 2

└── Version 3
```

Each upload creates a new object version instead of replacing the existing one.

---

# Benefits of Versioning

Versioning protects against:

- Accidental deletion
- Accidental overwrite
- Application bugs
- User mistakes
- Ransomware recovery

It is strongly recommended for production buckets.

---

# Checking Versioning Status

```bash
aws s3api get-bucket-versioning \
--bucket company-backups
```

Example:

```json
{
    "Status":"Enabled"
}
```

Possible values:

- Enabled
- Suspended
- Not Configured

---

# Enable Versioning

```bash
aws s3api put-bucket-versioning \
--bucket company-backups \
--versioning-configuration Status=Enabled
```

Once enabled, every object receives a unique Version ID.

---

# Suspend Versioning

```bash
aws s3api put-bucket-versioning \
--bucket company-backups \
--versioning-configuration Status=Suspended
```

Suspending versioning prevents new versions from being created but does not delete existing versions.

---

# Understanding Version IDs

Example:

```text
report.pdf

↓

Version ID:
3HL4kqtJlcpXrof3...
```

Every version has its own unique identifier.

Applications can retrieve specific versions when needed.

---

# Listing Object Versions

```bash
aws s3api list-object-versions \
--bucket company-backups
```

Example output:

```json
{
    "Versions":[
        {
            "Key":"report.pdf",
            "VersionId":"3HL4..."
        }
    ]
}
```

---

# Delete Markers

Deleting an object in a versioned bucket does **not** immediately remove the data.

Instead:

```text
Delete Object

↓

Delete Marker Created

↓

Object Hidden

↓

Previous Versions Still Exist
```

This allows recovery of deleted objects.

---

# Recovering Deleted Objects

If a Delete Marker exists:

1. Remove the Delete Marker.
2. Previous object versions become visible again.

This is one of Versioning's greatest advantages.

---

# Lifecycle Rules

Lifecycle Rules automatically manage objects throughout their lifecycle.

Examples:

- Move old data to cheaper storage.
- Delete expired objects.
- Archive backups.
- Reduce storage costs.

Lifecycle management eliminates manual housekeeping.

---

# Viewing Lifecycle Rules

```bash
aws s3api get-bucket-lifecycle-configuration \
--bucket company-backups
```

---

# Applying Lifecycle Rules

```bash
aws s3api put-bucket-lifecycle-configuration \
--bucket company-backups \
--lifecycle-configuration file://lifecycle.json
```

Lifecycle configurations are typically stored in JSON files.

---

# Example Lifecycle Rule

```json
{
    "Rules":[
        {
            "ID":"ArchiveLogs",
            "Status":"Enabled",
            "Filter":{
                "Prefix":"logs/"
            },
            "Transitions":[
                {
                    "Days":30,
                    "StorageClass":"STANDARD_IA"
                }
            ]
        }
    ]
}
```

After 30 days, log files automatically move to **STANDARD_IA**.

---

# Lifecycle Actions

Lifecycle Rules support:

- Transition
- Expiration
- Delete expired versions
- Abort incomplete multipart uploads

Automation reduces operational overhead.

---

# Transitioning Objects

Common transition strategy:

```text
Upload

↓

30 Days

↓

STANDARD_IA

↓

90 Days

↓

GLACIER_IR

↓

365 Days

↓

DEEP_ARCHIVE
```

Data becomes progressively cheaper to store.

---

# Object Expiration

Automatically delete objects after a specified period.

Example:

```text
Temporary Files

↓

30 Days

↓

Deleted Automatically
```

Useful for:

- Logs
- Temporary uploads
- Build artifacts
- Cache files

---

# Storage Classes

Amazon S3 provides multiple Storage Classes.

| Storage Class | Best For |
|---------------|----------|
| STANDARD | Frequently accessed data |
| STANDARD_IA | Infrequent access |
| ONEZONE_IA | Non-critical infrequent access |
| INTELLIGENT_TIERING | Unknown access patterns |
| GLACIER_IR | Archive with instant retrieval |
| GLACIER Flexible Retrieval | Long-term archives |
| DEEP_ARCHIVE | Compliance and long-term retention |

Choosing the correct Storage Class balances performance and cost.

---

# Storage Class Comparison

| Storage Class | Retrieval Speed | Storage Cost | Retrieval Cost |
|---------------|----------------|-------------|----------------|
| STANDARD | Milliseconds | High | None |
| STANDARD_IA | Milliseconds | Lower | Yes |
| INTELLIGENT_TIERING | Milliseconds | Medium | Minimal |
| GLACIER_IR | Milliseconds | Low | Yes |
| GLACIER Flexible Retrieval | Minutes to Hours | Very Low | Yes |
| DEEP_ARCHIVE | Hours | Lowest | Yes |

---

# Intelligent-Tiering

Ideal when access patterns are unpredictable.

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--storage-class INTELLIGENT_TIERING
```

Amazon S3 automatically moves objects between access tiers.

---

# Glacier Storage

Best suited for:

- Compliance
- Legal records
- Financial archives
- Medical records
- Historical backups

Glacier significantly reduces storage costs at the expense of retrieval speed.

---

# Choosing the Right Storage Class

| Workload | Recommended Class |
|----------|-------------------|
| Website Assets | STANDARD |
| Daily Backups | STANDARD_IA |
| Application Logs | INTELLIGENT_TIERING |
| Monthly Reports | GLACIER_IR |
| Compliance Archives | DEEP_ARCHIVE |

---

# Cost Optimization Tips

To reduce S3 costs:

- Enable Lifecycle Rules.
- Transition inactive objects.
- Delete temporary files automatically.
- Use Intelligent-Tiering for unpredictable workloads.
- Archive compliance data.
- Review storage usage regularly.

---

# Backup Strategy

A common production strategy:

```text
Production Data

↓

Versioning Enabled

↓

Daily Backup

↓

Lifecycle Rule

↓

Archive

↓

Delete After Retention Period
```

This provides both protection and cost efficiency.

---

# Production Workflow

Example:

```text
Create Bucket
      │
      ▼
Enable Versioning
      │
      ▼
Enable Encryption
      │
      ▼
Configure Lifecycle Rules
      │
      ▼
Choose Storage Class
      │
      ▼
Upload Objects
      │
      ▼
Monitor Storage Costs
```

---

# Common Mistakes

## Versioning Is Not a Backup

Versioning protects against accidental deletion and overwrites.

It does **not** replace a comprehensive backup strategy or cross-region disaster recovery.

---

## Forgetting Lifecycle Rules

Leaving old objects in STANDARD storage indefinitely can significantly increase storage costs.

---

## Choosing the Wrong Storage Class

Storing frequently accessed objects in Glacier may result in high retrieval costs and delayed access.

---

# Production Best Practices

- Enable Versioning for production buckets.
- Use Lifecycle Rules to automate storage management.
- Transition old data to cheaper storage.
- Archive compliance data appropriately.
- Review storage costs regularly.
- Test recovery procedures periodically.
- Combine Versioning with Cross-Region Replication for critical workloads.

---

# Architecture Note

```text
Upload Object
      │
      ▼
Versioning
      │
      ▼
Lifecycle Rules
      │
      ▼
Storage Class Transition
      │
      ▼
Archive
      │
      ▼
Expiration
```

Amazon S3 automatically manages objects according to your lifecycle configuration.

---

# Interview Note

### Question

**What is the difference between Versioning and Lifecycle Rules?**

### Answer

Versioning protects objects by maintaining multiple versions, allowing recovery from accidental deletions or overwrites. Lifecycle Rules automate object management by transitioning objects between Storage Classes or deleting them after a defined period. Versioning focuses on data protection, while Lifecycle Rules focus on automation and cost optimization.

---

# Key Takeaways

- Enable Versioning to protect against accidental data loss.
- Use Lifecycle Rules to automate storage management.
- Choose Storage Classes based on access patterns.
- Use Intelligent-Tiering when access patterns are unpredictable.
- Archive long-term data using Glacier or Deep Archive.
- Regularly review storage costs and lifecycle policies.
- Combine Versioning, Lifecycle Rules, and appropriate Storage Classes for a resilient and cost-effective storage strategy.

---
