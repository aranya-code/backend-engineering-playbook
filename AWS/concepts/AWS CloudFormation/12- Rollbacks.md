# CloudFormation Rollbacks

## What is a Rollback?

A Rollback is CloudFormation's recovery mechanism that automatically restores infrastructure to its previous stable state when a stack operation fails.

Think of Rollback as:

```text
Undo Operation
Recovery Process
Safety Mechanism
```

for CloudFormation.

---

# Why Rollbacks Exist

Imagine CloudFormation is creating:

```text
VPC
 ↓
Subnet
 ↓
Security Group
 ↓
EC2 Instance
```

The EC2 creation fails.

Without Rollback:

```text
VPC       ✅
Subnet    ✅
SG        ✅
EC2       ❌
```

Partial infrastructure remains.

This creates:

* Orphaned resources
* Inconsistent environments
* Additional costs
* Operational complexity

CloudFormation Rollback solves this problem.

---

# How Rollback Works

```text
Create Stack
      │
      ▼
Create Resources
      │
      ▼
Failure Detected
      │
      ▼
Rollback Triggered
      │
      ▼
Delete Created Resources
      │
      ▼
Restore Previous State
```

---

# Rollback During Stack Creation

Example:

Template:

```text
VPC
Subnet
EC2
RDS
```

Creation Process:

```text
VPC      ✅
Subnet   ✅
EC2      ❌
RDS      Not Started
```

CloudFormation automatically:

```text
Delete EC2
Delete Subnet
Delete VPC
```

Result:

```text
No Resources Left
```

Stack Status:

```text
ROLLBACK_COMPLETE
```

---

# Rollback During Stack Update

Before Update:

```text
Production Stack

VPC
EC2
ALB
RDS
```

New update introduces an error.

Example:

```text
Invalid Security Group
```

CloudFormation:

```text
UPDATE_IN_PROGRESS
        ↓
UPDATE_FAILED
        ↓
UPDATE_ROLLBACK_IN_PROGRESS
        ↓
UPDATE_ROLLBACK_COMPLETE
```

Infrastructure returns to its previous working state.

---

# Rollback Lifecycle

## Creation Failure

```text
CREATE_IN_PROGRESS
        ↓
CREATE_FAILED
        ↓
ROLLBACK_IN_PROGRESS
        ↓
ROLLBACK_COMPLETE
```

---

## Update Failure

```text
UPDATE_IN_PROGRESS
        ↓
UPDATE_FAILED
        ↓
UPDATE_ROLLBACK_IN_PROGRESS
        ↓
UPDATE_ROLLBACK_COMPLETE
```

---

# Common Rollback States

| Status                      | Meaning                     |
| --------------------------- | --------------------------- |
| ROLLBACK_IN_PROGRESS        | Creation rollback running   |
| ROLLBACK_COMPLETE           | Creation rollback completed |
| ROLLBACK_FAILED             | Rollback failed             |
| UPDATE_ROLLBACK_IN_PROGRESS | Update rollback running     |
| UPDATE_ROLLBACK_COMPLETE    | Update rollback completed   |
| UPDATE_ROLLBACK_FAILED      | Update rollback failed      |

---

# Example: Invalid AMI

Template:

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      ImageId: ami-invalid
```

CloudFormation:

```text
Create EC2
      ↓
AMI Not Found
      ↓
CREATE_FAILED
      ↓
ROLLBACK_IN_PROGRESS
```

Result:

```text
Stack Cleaned Up
```

---

# Example: Duplicate S3 Bucket

Template:

```yaml
BucketName: company-production-bucket
```

Existing bucket already exists.

CloudFormation:

```text
Bucket Creation Failed
         ↓
ROLLBACK_IN_PROGRESS
```

Previously created resources are removed.

---

# Disabling Rollback

During stack creation:

AWS Console:

```text
Disable Rollback
```

Option can be enabled.

---

CLI:

```bash
aws cloudformation create-stack \
--stack-name demo-stack \
--disable-rollback
```

---

# Why Disable Rollback?

Useful for troubleshooting.

Normal behavior:

```text
Resource Failed
      ↓
Deleted Automatically
```

Difficult to investigate.

With rollback disabled:

```text
Resource Failed
      ↓
Resources Remain
```

Allows debugging.

---

# Example

Without Disable Rollback:

```text
EC2 Failed
     ↓
Deleted
```

No logs available.

---

With Disable Rollback:

```text
EC2 Failed
     ↓
Instance Remains
```

You can inspect:

* Console Logs
* Security Groups
* IAM Permissions
* User Data

---

# Rollback Triggers

CloudFormation can monitor CloudWatch Alarms.

If alarm enters:

```text
ALARM State
```

CloudFormation automatically rolls back.

---

# Architecture

```text
CloudFormation
       │
       ▼
CloudWatch Alarm
       │
       ▼
Application Failure
       │
       ▼
Rollback Triggered
```

---

# Example Use Case

Deployment:

```text
EC2
ALB
Auto Scaling
```

Alarm:

```text
HTTP 5xx Errors > 100
```

During deployment:

```text
Alarm Triggered
       ↓
CloudFormation Rollback
```

Infrastructure returns to previous state.

---

# Continue Update Rollback

Sometimes rollback itself fails.

Status:

```text
UPDATE_ROLLBACK_FAILED
```

Stack becomes stuck.

---

# Causes

Example:

```text
Resource Deleted Manually
Dependency Missing
Permission Issue
```

CloudFormation cannot complete rollback.

---

# Recovery Command

```bash
aws cloudformation continue-update-rollback \
--stack-name production-stack
```

CloudFormation attempts to complete rollback.

---

# Stack Recovery Workflow

```text
UPDATE_FAILED
       ↓
UPDATE_ROLLBACK_FAILED
       ↓
Fix Issue
       ↓
continue-update-rollback
       ↓
UPDATE_ROLLBACK_COMPLETE
```

---

# Viewing Rollback Events

Console:

```text
CloudFormation
      ↓
Stack
      ↓
Events
```

Look for:

```text
CREATE_FAILED
UPDATE_FAILED
ROLLBACK_IN_PROGRESS
```

These events usually contain the root cause.

---

# Example Event Log

```text
CREATE_IN_PROGRESS

Create EC2

CREATE_FAILED

AMI ami-invalid not found

ROLLBACK_IN_PROGRESS

Delete EC2

ROLLBACK_COMPLETE
```

The failure reason is visible.

---

# Rollback vs Change Sets

| Feature          | Rollback | Change Set |
| ---------------- | -------- | ---------- |
| Prevents Failure | ❌        | ✅          |
| Recovers Failure | ✅        | ❌          |
| Preview Changes  | ❌        | ✅          |
| Automatic        | ✅        | ❌          |

---

# Rollback vs Drift Detection

| Feature              | Rollback | Drift Detection |
| -------------------- | -------- | --------------- |
| Recovery             | ✅        | ❌               |
| Compare Actual State | ❌        | ✅               |
| Automatic            | ✅        | ❌               |

---

# Real-World Example

Production Update:

Current:

```text
ALB
EC2
RDS
```

Developer updates:

```text
Database Configuration
```

CloudFormation:

```text
UPDATE_IN_PROGRESS
```

Database modification fails.

CloudFormation:

```text
UPDATE_FAILED
```

Automatic recovery:

```text
UPDATE_ROLLBACK_IN_PROGRESS
```

Final state:

```text
UPDATE_ROLLBACK_COMPLETE
```

Production continues using the old configuration.

---

# Rollback Best Practices

## Keep Rollback Enabled

Never disable rollback in production.

---

## Use Disable Rollback Only for Debugging

Development environments only.

---

## Review Events Carefully

Most rollback root causes appear in:

```text
Stack Events
```

---

## Use Change Sets

Prevent rollback situations by reviewing changes beforehand.

---

## Use CloudWatch Alarms

Combine with rollback triggers for safer deployments.

---

# Common Mistakes

## Ignoring Root Cause

Rollback is a symptom.

Find the actual error:

```text
CREATE_FAILED
UPDATE_FAILED
```

event.

---

## Disabling Rollback in Production

Can leave partially deployed infrastructure.

---

## Manual Resource Deletion

May cause:

```text
UPDATE_ROLLBACK_FAILED
```

during recovery.

---

## Ignoring UPDATE_ROLLBACK_COMPLETE

Stack is usable again but update did not succeed.

Investigate before retrying.

---

# Troubleshooting Workflow

```text
Stack Failed
      │
      ▼
Check Events
      │
      ▼
Find CREATE_FAILED
or
UPDATE_FAILED
      │
      ▼
Fix Root Cause
      │
      ▼
Retry Deployment
```

---

# Key Takeaways

* Rollback is CloudFormation's automatic recovery mechanism.
* Prevents partially deployed infrastructure.
* Creation failures trigger:

  * ROLLBACK_IN_PROGRESS
  * ROLLBACK_COMPLETE
* Update failures trigger:

  * UPDATE_ROLLBACK_IN_PROGRESS
  * UPDATE_ROLLBACK_COMPLETE
* Disable Rollback is useful only for debugging.
* Continue Update Rollback helps recover stuck stacks.
* Rollback events are critical for troubleshooting.
* Understanding rollback behavior is essential for production CloudFormation deployments.

---

# Interview Questions

### What is a CloudFormation Rollback?

Rollback is the automatic process of restoring a stack to its previous stable state after a failure.

---

### What triggers a rollback?

Common causes:

* Invalid AMI
* Permission Issues
* Resource Conflicts
* Invalid Parameters
* Dependency Failures

---

### What is UPDATE_ROLLBACK_COMPLETE?

A stack update failed and CloudFormation successfully restored the previous working state.

---

### Why would you disable rollback?

For debugging failed resource deployments.

---

### What is UPDATE_ROLLBACK_FAILED?

CloudFormation failed while attempting to roll back an update.

---

### How do you recover from UPDATE_ROLLBACK_FAILED?

```bash
aws cloudformation continue-update-rollback \
--stack-name my-stack
```

---

### Should rollback be disabled in production?

No.

Rollback should remain enabled in production environments to ensure automatic recovery.
