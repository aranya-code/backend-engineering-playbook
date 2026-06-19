# ECS Storage

# Why Storage Matters

Containers are designed to be:

```text
Disposable
Ephemeral
Replaceable
```

This creates a challenge.

What happens when:

```text
Container Stops
```

and application data exists inside the container?

The data is lost.

Understanding storage is critical for production ECS workloads.

---

# Container Storage Fundamentals

Every container has a writable layer.

Example:

```text
Container
   ↓
Writable Layer
```

Files written here exist only while the container exists.

---

# Ephemeral Storage

Ephemeral means:

```text
Temporary
```

Example:

```text
Task Starts
```

Creates storage.

---

```text
Task Stops
```

Storage disappears.

---

# Example

Inside a container:

```bash
echo "Hello" > file.txt
```

If the container is destroyed:

```text
file.txt
```

is lost.

---

# Characteristics of Ephemeral Storage

Advantages:

- Fast
- Simple
- No additional cost

---

Disadvantages:

- Data loss
- No sharing
- Not persistent

---

# Good Use Cases

Examples:

- Temporary files
- Caches
- Processing jobs
- Intermediate results

---

# Bad Use Cases

Avoid for:

- User uploads
- Databases
- Reports
- Business-critical data

---

# Persistent Storage

Persistent storage survives container restarts.

Benefits:

```text
Task Restart
      ↓
Data Still Exists
```

---

# Storage Options in ECS

Common options:

```text
EFS
EBS
S3
Ephemeral Storage
```

Each serves a different purpose.

---

# Amazon EFS

Elastic File System (EFS) is a managed network file system.

Supports:

```text
NFS
```

protocol.

---

# EFS Architecture

```text
Task A
   ↓
   EFS
   ↑
Task B
```

Multiple tasks can access the same data.

---

# Why Use EFS?

Provides:

- Shared storage
- Persistent storage
- Multi-AZ availability
- Managed infrastructure

---

# ECS + EFS

Supported by:

```text
EC2
Fargate
```

launch types.

---

# Common EFS Use Cases

Examples:

- User uploads
- Shared reports
- Static assets
- ML models
- Configuration files

---

# EFS Advantages

## Shared Access

Multiple tasks can read/write.

---

## Highly Available

Multi-AZ architecture.

---

## Managed Service

No server management.

---

## Automatic Scaling

Storage grows automatically.

---

# EFS Disadvantages

## Higher Latency

Compared to local disks.

---

## Higher Cost

Compared to EBS.

---

## Not Ideal for Databases

Databases need low latency.

---

# Amazon EBS

Elastic Block Store (EBS) provides block storage.

Think:

```text
Virtual Hard Drive
```

---

# EBS Architecture

```text
EC2 Instance
      ↓
EBS Volume
```

---

# EBS Characteristics

Provides:

- High performance
- Low latency
- Persistent storage

---

# EBS Advantages

## Fast Storage

Excellent performance.

---

## Low Latency

Suitable for demanding workloads.

---

## Multiple Volume Types

Examples:

```text
gp3
io2
st1
```

---

# EBS Limitations

## Not Shared

Typically attached to one instance.

---

## EC2 Only

Not directly supported by Fargate.

---

## AZ Bound

Lives within a specific availability zone.

---

# EFS vs EBS

| Feature | EFS | EBS |
|----------|------|------|
| Shared Storage | Yes | No |
| Multi-AZ | Yes | No |
| Performance | Medium | High |
| Fargate Support | Yes | No |
| Cost | Higher | Lower |
| Use Case | Shared Files | High Performance Storage |

---

# Amazon S3

S3 is:

```text
Object Storage
```

Not a file system.

---

# Important Interview Question

Can ECS mount S3 directly?

Answer:

```text
No
```

S3 is not a POSIX file system.

---

# ECS + S3 Pattern

Applications access S3 via APIs.

Example:

```python
import boto3

s3 = boto3.client("s3")
```

---

# Architecture

```text
ECS Task
      ↓
S3 API
      ↓
S3 Bucket
```

---

# Common S3 Use Cases

Examples:

- User uploads
- Backups
- Reports
- Media storage

---

# Fargate Storage

Fargate provides:

```text
Ephemeral Storage
```

by default.

---

Default:

```text
20 GB
```

Configurable for larger workloads.

---

# Fargate Storage Use Cases

Examples:

- Temporary processing
- Data transformation
- Batch jobs

---

# Shared Storage Architecture

Example:

```text
Task A
Task B
Task C
    ↓
    EFS
```

All tasks access shared files.

---

# Backup and Recovery

Storage should be backed up.

Examples:

```text
EFS Backup
EBS Snapshot
S3 Versioning
```

---

# EBS Snapshots

Create point-in-time backups.

Architecture:

```text
EBS
 ↓
Snapshot
 ↓
S3 Managed Storage
```

---

# EFS Backup

AWS Backup supports:

```text
Automated Backups
```

for EFS.

---

# Encryption

Always encrypt storage.

---

# EFS Encryption

Supports:

```text
Encryption At Rest
Encryption In Transit
```

---

# EBS Encryption

Supports:

```text
KMS Encryption
```

---

# S3 Encryption

Options:

```text
SSE-S3
SSE-KMS
```

---

# Production Use Cases

## User Upload Platform

```text
ECS
 ↓
S3
```

Store uploaded files.

---

## Shared Reports

```text
ECS
 ↓
EFS
```

Shared access.

---

## Analytics Processing

```text
ECS
 ↓
Ephemeral Storage
```

Temporary data.

---

# Common Storage Mistakes

## Storing Data Inside Containers

Problem:

```text
Task Restart
     ↓
Data Lost
```

---

## Using EFS for Databases

Problem:

Performance limitations.

---

## No Backups

Risk:

Data loss.

---

## No Encryption

Risk:

Data exposure.

---

# Troubleshooting Checklist

Check:

```text
EFS Mount Targets
Security Groups
IAM Permissions
Storage Limits
Encryption Settings
```

---

# Common Interview Questions

## What is Ephemeral Storage?

Temporary storage removed when the task stops.

---

## Difference Between EFS and EBS?

EFS:

Shared file storage.

EBS:

High-performance block storage.

---

## Can ECS Mount S3?

Not directly.

Applications use APIs.

---

## Why Use EFS?

Shared persistent storage.

---

## Why Avoid Databases on EFS?

Higher latency.

---

# Senior Engineer Perspective

Storage decisions impact:

- Availability
- Cost
- Performance
- Scalability

Most containerized applications should treat containers as disposable and store important data externally.

Rule of thumb:

```text
Application State
      ↓
External Storage

Application Logic
      ↓
Containers
```

Keeping these concerns separate improves resilience and scalability.

---

# Key Takeaways

- Containers are ephemeral.
- Persistent data should live outside containers.
- EFS provides shared file storage.
- EBS provides high-performance block storage.
- S3 provides object storage.
- Fargate includes ephemeral storage.
- Backups and encryption are critical for production systems.
