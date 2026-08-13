# AMIs, Volumes & Snapshots

> Learn how to create and manage Amazon Machine Images (AMIs), Elastic Block Store (EBS) volumes, and snapshots using the AWS CLI. This chapter covers backup strategies, disaster recovery, and production storage management.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon Machine Images (AMIs)
- Create custom AMIs
- Launch instances from AMIs
- Manage EBS volumes
- Attach and detach volumes
- Resize EBS volumes
- Create and restore snapshots
- Build backup and disaster recovery strategies

---

# Understanding Amazon Machine Images (AMIs)

An Amazon Machine Image (AMI) is a template used to launch EC2 instances.

An AMI contains:

- Operating System
- Installed Software
- Configuration
- Root Volume Snapshot
- Launch Permissions

Think of an AMI as a reusable server template.

---

# EC2 Storage Architecture

```text
AMI
 │
 ▼
Launch Instance
 │
 ▼
Root EBS Volume
 │
 ▼
Additional EBS Volumes
 │
 ▼
Snapshots
```

AMIs define how an instance starts, while EBS volumes store persistent data.

---

# Listing Available AMIs

List Amazon-owned Linux AMIs:

```bash
aws ec2 describe-images \
--owners amazon
```

The output can be large, so filtering is recommended.

---

# Filter by AMI Name

Example:

```bash
aws ec2 describe-images \
--owners amazon \
--filters "Name=name,Values=amzn2-*"
```

Useful for finding Amazon Linux 2 images.

---

# View a Specific AMI

```bash
aws ec2 describe-images \
--image-ids ami-0123456789abcdef0
```

Returns:

- AMI ID
- Name
- Creation Date
- Architecture
- Virtualization Type
- Block Device Mapping

---

# Creating a Custom AMI

Create an image from an existing EC2 instance.

```bash
aws ec2 create-image \
--instance-id i-0123456789abcdef0 \
--name "backend-server-v1"
```

AWS creates:

- AMI
- Root volume snapshot

This is commonly used before deployments.

---

# Viewing Custom AMIs

```bash
aws ec2 describe-images \
--owners self
```

Lists every AMI owned by your AWS account.

---

# Deregistering an AMI

Remove an unused AMI.

```bash
aws ec2 deregister-image \
--image-id ami-0123456789abcdef0
```

Note:

Deregistering an AMI does **not** delete the underlying snapshot.

---

# Understanding Amazon EBS

Amazon Elastic Block Store (EBS) provides persistent block storage for EC2.

Characteristics:

- Persistent
- Durable
- Encrypted (optional)
- Network attached
- Independent of EC2 lifecycle

---

# Common EBS Volume Types

| Volume Type | Best For |
|-------------|----------|
| gp3 | General-purpose SSD |
| io2 | High-performance databases |
| st1 | Throughput-intensive HDD |
| sc1 | Cold HDD |
| io1 | Provisioned IOPS SSD |

Most production workloads use **gp3**.

---

# Listing Volumes

```bash
aws ec2 describe-volumes
```

---

# Describe a Specific Volume

```bash
aws ec2 describe-volumes \
--volume-ids vol-0123456789abcdef0
```

Returns:

- Size
- Type
- State
- Availability Zone
- Encryption
- Attachments

---

# Creating an EBS Volume

```bash
aws ec2 create-volume \
--availability-zone ap-south-1a \
--size 20 \
--volume-type gp3
```

Creates a 20 GB General Purpose SSD volume.

---

# Attaching a Volume

```bash
aws ec2 attach-volume \
--volume-id vol-0123456789abcdef0 \
--instance-id i-0123456789abcdef0 \
--device /dev/xvdf
```

The instance can now use the attached volume.

---

# Detaching a Volume

```bash
aws ec2 detach-volume \
--volume-id vol-0123456789abcdef0
```

Always unmount the filesystem inside the operating system before detaching the volume to prevent data corruption.

---

# Modifying Volume Size

Increase volume size.

```bash
aws ec2 modify-volume \
--volume-id vol-0123456789abcdef0 \
--size 100
```

After increasing the size, expand the filesystem inside the instance.

---

# Viewing Volume Attachments

```bash
aws ec2 describe-volumes \
--query "Volumes[].Attachments"
```

Useful when investigating storage issues.

---

# Understanding Snapshots

Snapshots are point-in-time backups of EBS volumes.

Benefits:

- Incremental
- Durable
- Stored in Amazon S3 internally
- Used for backups
- Used for disaster recovery

---

# Snapshot Architecture

```text
EBS Volume
      │
      ▼
Snapshot
      │
      ▼
Restore
      │
      ▼
New Volume
```

Snapshots never modify the original volume.

---

# Creating a Snapshot

```bash
aws ec2 create-snapshot \
--volume-id vol-0123456789abcdef0 \
--description "Daily Backup"
```

AWS creates a snapshot asynchronously.

---

# Listing Snapshots

```bash
aws ec2 describe-snapshots \
--owner-ids self
```

---

# Describe a Snapshot

```bash
aws ec2 describe-snapshots \
--snapshot-ids snap-0123456789abcdef0
```

Returns:

- Snapshot ID
- State
- Progress
- Start Time
- Volume Size

---

# Restoring a Volume

Create a new EBS volume from a snapshot.

```bash
aws ec2 create-volume \
--snapshot-id snap-0123456789abcdef0 \
--availability-zone ap-south-1a
```

This is the standard recovery workflow.

---

# Deleting a Snapshot

```bash
aws ec2 delete-snapshot \
--snapshot-id snap-0123456789abcdef0
```

Do not delete snapshots that are still required for AMIs or backup retention.

---

# Backup Strategy

Recommended production workflow:

```text
Running Instance
        │
        ▼
EBS Volume
        │
        ▼
Daily Snapshot
        │
        ▼
Lifecycle Policy
        │
        ▼
Archive
```

Automated snapshots provide reliable recovery points.

---

# Disaster Recovery Workflow

```text
Instance Failure
        │
        ▼
Locate Snapshot
        │
        ▼
Create New Volume
        │
        ▼
Attach Volume
        │
        ▼
Launch Replacement Instance
```

Snapshots significantly reduce recovery time.

---

# Common Errors

## Incorrect Availability Zone

Volumes can only be attached to instances in the same Availability Zone.

Verify:

```bash
aws ec2 describe-volumes
```

and

```bash
aws ec2 describe-instances
```

---

## VolumeInUse

Example:

```text
VolumeInUse
```

Detach the volume before deleting or reattaching it.

---

## InvalidSnapshot.NotFound

Verify the Snapshot ID:

```bash
aws ec2 describe-snapshots \
--owner-ids self
```

---

# Production Best Practices

- Use **gp3** volumes for most workloads.
- Encrypt EBS volumes.
- Automate snapshot creation.
- Test snapshot restoration regularly.
- Tag volumes and snapshots consistently.
- Delete obsolete snapshots to reduce storage costs.
- Never rely on snapshots as the only disaster recovery strategy.

---

# Real-World Workflow

Creating a production backup.

```text
Running EC2
      │
      ▼
Create Snapshot
      │
      ▼
Verify Completion
      │
      ▼
Copy to DR Region (Optional)
      │
      ▼
Retention Policy
```

---

# Architecture Note

```text
AMI
 │
 ▼
EC2 Instance
 │
 ▼
EBS Volume
 │
 ▼
Snapshot
 │
 ▼
Restore
 │
 ▼
New Volume
```

AMIs define compute configuration, while EBS volumes and snapshots provide persistent storage and recovery capabilities.

---

# Interview Note

### Question

**What is the difference between an AMI and an EBS Snapshot?**

### Answer

An **AMI** is a complete machine template used to launch EC2 instances. It includes the operating system, configuration, and references to snapshots of the root volume. An **EBS Snapshot** is a point-in-time backup of an EBS volume that can be used to create new volumes. AMIs are primarily used for provisioning servers, while snapshots are used for backup and disaster recovery.

---

# Key Takeaways

- AMIs are templates used to launch EC2 instances.
- EBS volumes provide persistent block storage.
- Snapshots are incremental backups of EBS volumes.
- Volumes and instances must reside in the same Availability Zone for attachment.
- Use snapshots as part of a comprehensive backup strategy.
- Encrypt storage and automate backups in production.
- Regularly test restore procedures to ensure disaster recovery readiness.

---

