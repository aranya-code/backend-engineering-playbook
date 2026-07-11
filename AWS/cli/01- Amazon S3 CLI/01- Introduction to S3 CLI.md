# Introduction to S3 CLI

> Learn how to use the AWS CLI to interact with Amazon S3, understand the difference between high-level and low-level S3 commands, and build a strong foundation before managing buckets and objects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand how the AWS CLI interacts with Amazon S3.
- Differentiate between high-level and low-level S3 commands.
- Navigate the two S3 command families.
- Execute common read-only S3 operations.
- Understand S3 URI syntax.
- Identify when to use `aws s3` versus `aws s3api`.

---

# Why Learn S3 CLI?

Amazon S3 is one of the most frequently used AWS services.

Backend engineers use S3 CLI for:

- Uploading build artifacts
- Downloading backups
- Managing application assets
- Log archival
- Static website deployment
- CI/CD pipelines
- Disaster recovery
- Data migration

Most production environments interact with S3 through automation rather than the AWS Management Console.

---

# AWS CLI Supports Two S3 Interfaces

This is one of the most important concepts to understand.

AWS CLI provides **two different command families** for Amazon S3.

```text
AWS CLI
│
├── aws s3
│
└── aws s3api
```

Although both communicate with Amazon S3, they serve different purposes.

---

# High-Level Commands (`aws s3`)

The `aws s3` command family provides simplified commands for common file operations.

Examples:

```bash
aws s3 ls
```

```bash
aws s3 cp file.txt s3://my-bucket/
```

```bash
aws s3 sync ./build s3://frontend-assets/
```

Characteristics:

- Easy to use
- Human-friendly syntax
- Recursive operations
- Built-in synchronization
- Ideal for everyday tasks

This is the interface most engineers use daily.

---

# Low-Level Commands (`aws s3api`)

The `aws s3api` command family maps closely to the underlying Amazon S3 APIs.

Example:

```bash
aws s3api list-buckets
```

```bash
aws s3api create-bucket \
    --bucket my-company-assets
```

Characteristics:

- Direct API access
- Full feature coverage
- JSON-based requests and responses
- Greater control
- Better suited for automation and advanced operations

If a new S3 feature is released, it usually appears in `s3api` before high-level commands.

---

# `aws s3` vs `aws s3api`

| Feature | `aws s3` | `aws s3api` |
|----------|----------|-------------|
| Learning Curve | Easy | Moderate |
| Human-Friendly | ✅ | ❌ |
| Recursive Copy | ✅ | ❌ |
| Sync Support | ✅ | ❌ |
| JSON Output | Limited | Full |
| Direct API Mapping | ❌ | ✅ |
| Automation | Good | Excellent |
| Advanced Features | Limited | Full |

---

# Which One Should You Use?

General recommendation:

| Task | Recommended Command |
|------|----------------------|
| Upload files | `aws s3` |
| Download files | `aws s3` |
| Synchronize directories | `aws s3` |
| List buckets | Either |
| Configure bucket settings | `aws s3api` |
| Manage versioning | `aws s3api` |
| Configure lifecycle rules | `aws s3api` |
| Enable encryption | `aws s3api` |

A practical rule of thumb is:

> Use **`aws s3`** for file operations and **`aws s3api`** for resource configuration.

---

# Understanding S3 URIs

Amazon S3 resources are referenced using **S3 URIs**.

General format:

```text
s3://bucket-name
```

Bucket example:

```text
s3://company-backups
```

Object example:

```text
s3://company-backups/database/backup.sql
```

Folder-like prefix example:

```text
s3://company-backups/logs/2026/
```

Remember:

> Amazon S3 has **buckets and objects**. "Folders" are logical prefixes used for organization.

---

# Your First S3 Command

List all buckets in your AWS account:

```bash
aws s3 ls
```

Example output:

```text
2026-01-12 09:10:45 company-backups
2026-03-18 14:22:11 frontend-assets
2026-05-02 16:30:07 application-logs
```

This is often the first command engineers execute when verifying S3 access.

---

# Listing Objects in a Bucket

Display objects inside a bucket:

```bash
aws s3 ls s3://company-backups
```

Recursive listing:

```bash
aws s3 ls s3://company-backups \
    --recursive
```

This command displays every object stored within the bucket.

---

# Common Global Options with S3

S3 commands support all AWS CLI global options.

Examples:

```bash
aws s3 ls \
    --profile production
```

```bash
aws s3 ls \
    --region ap-south-1
```

```bash
aws s3 ls \
    --no-cli-pager
```

These options behave exactly as described in the **CLI Basics** section.

---

# Production Tip

Always verify the active AWS account before modifying buckets.

```bash
aws sts get-caller-identity
```

A surprising number of production incidents occur because engineers unknowingly perform operations in the wrong AWS account.

---

# Architecture Note

Both command families ultimately communicate with the same Amazon S3 service.

```text
Developer
      │
      ▼
AWS CLI
      │
      ├── aws s3
      │
      └── aws s3api
              │
              ▼
        Amazon S3 API
              │
              ▼
        Buckets & Objects
```

The difference lies in the level of abstraction, not the underlying service.

---

# Interview Note

### Question

**What is the difference between `aws s3` and `aws s3api`?**

**Answer**

`aws s3` provides high-level, user-friendly commands for common operations such as copying, syncing, and listing objects. `aws s3api` exposes the underlying S3 REST APIs directly, offering complete control over bucket configuration, lifecycle policies, encryption, versioning, and other advanced features. In practice, engineers typically use `aws s3` for day-to-day file operations and `aws s3api` for administrative and automation tasks.

---

# Key Takeaways

- AWS CLI provides two interfaces for Amazon S3.
- `aws s3` is optimized for everyday file operations.
- `aws s3api` exposes the complete S3 API.
- S3 resources are referenced using `s3://` URIs.
- Most engineers use both command families depending on the task.
- Understanding this distinction is the foundation for mastering S3 automation.

---
