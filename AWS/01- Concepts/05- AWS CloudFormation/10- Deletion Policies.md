# CloudFormation Deletion Policies

## What is a Deletion Policy?

A Deletion Policy controls what happens to a resource when:

* A Stack is deleted
* A Resource is removed from a template
* CloudFormation replaces a resource

Without a Deletion Policy, CloudFormation typically deletes the resource permanently.

---

# Why Deletion Policies Matter

Imagine a production stack contains:

```text
VPC
EC2
RDS Database
S3 Bucket
```

A developer accidentally deletes the stack.

Without Deletion Policy:

```text
VPC        Deleted
EC2        Deleted
RDS        Deleted
S3         Deleted
```

Potential data loss.

With Deletion Policy:

```text
VPC        Deleted
EC2        Deleted
RDS        Retained
S3         Retained
```

Critical data survives.

---

# How Deletion Policy Works

```text
Delete Stack
      │
      ▼
CloudFormation
      │
      ▼
Check DeletionPolicy
      │
      ▼
Apply Action
```

---

# Syntax

```yaml
Resources:

  ResourceName:

    Type: ResourceType

    DeletionPolicy: PolicyType
```

---

# Available Deletion Policies

CloudFormation supports:

| Policy   | Behavior                        |
| -------- | ------------------------------- |
| Delete   | Remove resource                 |
| Retain   | Keep resource                   |
| Snapshot | Create snapshot before deletion |

---

# Default Behavior

If no policy is specified:

```yaml
Resources:

  DemoBucket:

    Type: AWS::S3::Bucket
```

CloudFormation uses:

```text
Delete
```

implicitly.

---

# Delete Policy

## What is Delete?

CloudFormation permanently deletes the resource.

Example:

```yaml
Resources:

  DemoBucket:

    Type: AWS::S3::Bucket

    DeletionPolicy: Delete
```

---

## Behavior

```text
Delete Stack
      │
      ▼
Delete Resource
      │
      ▼
Resource Removed
```

---

## Use Cases

Suitable for:

* Development Resources
* Temporary Environments
* Test Infrastructure

Examples:

```text
Test EC2
Temporary Buckets
Sandbox Resources
```

---

# Retain Policy

## What is Retain?

CloudFormation removes the resource from stack management but does not delete the resource itself.

Example:

```yaml
Resources:

  ProductionBucket:

    Type: AWS::S3::Bucket

    DeletionPolicy: Retain
```

---

## Behavior

```text
Delete Stack
      │
      ▼
Remove Stack
      │
      ▼
Resource Remains
```

---

## Result

Stack:

```text
Deleted
```

Bucket:

```text
Still Exists
```

---

# Retain Example

```yaml
Resources:

  CustomerDataBucket:

    Type: AWS::S3::Bucket

    DeletionPolicy: Retain
```

Delete stack:

```text
Stack Removed
```

Bucket:

```text
customer-data-bucket
```

still exists.

---

# Why Retain is Important

Protects:

* Business Data
* Customer Files
* Audit Logs
* Databases

from accidental deletion.

---

# Snapshot Policy

## What is Snapshot?

CloudFormation creates a snapshot before deleting the resource.

Example:

```yaml
Resources:

  ProductionDB:

    Type: AWS::RDS::DBInstance

    DeletionPolicy: Snapshot
```

---

## Behavior

```text
Delete Stack
      │
      ▼
Create Snapshot
      │
      ▼
Delete Resource
```

---

## Result

```text
Database Deleted
```

but:

```text
Snapshot Preserved
```

---

# Resources Supporting Snapshot

Common resources:

| Resource Type    | Snapshot Support |
| ---------------- | ---------------- |
| RDS              | Yes              |
| EBS Volume       | Yes              |
| Redshift Cluster | Yes              |
| ElastiCache      | Yes              |
| Neptune          | Yes              |

---

# Example: RDS Snapshot

```yaml
Resources:

  ProductionDB:

    Type: AWS::RDS::DBInstance

    DeletionPolicy: Snapshot
```

Delete stack:

```text
RDS Snapshot Created
       ↓
Database Deleted
```

Recovery remains possible.

---

# Example: EBS Snapshot

```yaml
Resources:

  DataVolume:

    Type: AWS::EC2::Volume

    DeletionPolicy: Snapshot
```

Delete stack:

```text
EBS Snapshot Created
```

before deletion.

---

# DeletionPolicy vs UpdateReplacePolicy

Many engineers confuse these.

---

## DeletionPolicy

Controls behavior when:

```text
Stack Deleted
Resource Removed
```

---

## UpdateReplacePolicy

Controls behavior when:

```text
Resource Replaced During Update
```

---

# Example

Current:

```yaml
BucketName: old-bucket
```

Updated:

```yaml
BucketName: new-bucket
```

CloudFormation:

```text
Replace Resource
```

UpdateReplacePolicy decides what happens to the old resource.

---

# Using Both Together

```yaml
Resources:

  ProductionDB:

    Type: AWS::RDS::DBInstance

    DeletionPolicy: Snapshot

    UpdateReplacePolicy: Snapshot
```

---

## Benefits

```text
Delete Stack
      ↓
Snapshot Created

Resource Replacement
      ↓
Snapshot Created
```

Maximum protection.

---

# Real-World Example

Production Database:

```yaml
Resources:

  ProductionDB:

    Type: AWS::RDS
```
