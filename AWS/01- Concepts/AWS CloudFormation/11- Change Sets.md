# CloudFormation Change Sets

## What are Change Sets?

A Change Set is a preview of changes that CloudFormation will make to your stack before actually applying them.

Think of a Change Set as:

```text
Terraform Plan
Git Diff
Deployment Preview
```

for CloudFormation.

Instead of directly updating a stack, you can review the impact first.

---

# Why Use Change Sets?

Imagine updating a production stack.

Current Infrastructure:

```text
VPC
ALB
EC2
RDS
```

You modify the template.

Questions:

```text
Will EC2 restart?
Will RDS be replaced?
Will data be lost?
Will resources be deleted?
```

A Change Set answers these questions before deployment.

---

# How Change Sets Work

```text
Current Stack
      │
      ▼
Updated Template
      │
      ▼
Create Change Set
      │
      ▼
Preview Changes
      │
      ▼
Execute Change Set
```

---

# Benefits of Change Sets

## Risk Reduction

Understand impact before deployment.

---

## Safe Production Updates

Review changes before modifying live infrastructure.

---

## Compliance

Provides approval workflow.

---

## Team Collaboration

Developers and Cloud Engineers can review changes together.

---

## Visibility

Shows:

* Resources Added
* Resources Modified
* Resources Deleted

---

# Change Set Workflow

```text
Modify Template
       │
       ▼
Create Change Set
       │
       ▼
Review Changes
       │
       ▼
Approve
       │
       ▼
Execute
```

---

# Creating a Change Set

AWS Console:

```text
CloudFormation
      ↓
Select Stack
      ↓
Create Change Set
```

---

# AWS CLI

```bash
aws cloudformation create-change-set \
--stack-name production-stack \
--change-set-name update-v1 \
--template-body file://template.yaml
```

---

# Viewing a Change Set

CloudFormation compares:

```text
Current Template
       vs
New Template
```

and generates a report.

---

# Example

Current Template:

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: t2.micro
```

---

Updated Template:

```yaml
Resources:

  WebServer:

    Type: AWS::EC2::Instance

    Properties:

      InstanceType: t3.micro
```

---

Generated Change Set:

```text
Resource:
WebServer

Action:
Modify

Replacement:
False
```

---

# Change Set Actions

CloudFormation classifies changes into actions.

| Action | Meaning                  |
| ------ | ------------------------ |
| Add    | Create new resource      |
| Modify | Update resource          |
| Remove | Delete resource          |
| Import | Import existing resource |

---

# Add Action

Example:

Old Template:

```text
EC2
```

New Template:

```text
EC2
RDS
```

Change Set:

```text
RDS
Action: Add
```

CloudFormation will create RDS.

---

# Modify Action

Example:

```yaml
InstanceType:
  t2.micro
```

changed to

```yaml
InstanceType:
  t3.micro
```

Change Set:

```text
Action: Modify
```

---

# Remove Action

Old Template:

```text
EC2
RDS
```

New Template:

```text
EC2
```

Change Set:

```text
RDS

Action: Remove
```

RDS will be deleted.

---

# Import Action

Used when importing existing AWS resources into CloudFormation management.

Example:

```text
Existing S3 Bucket
```

becomes:

```text
CloudFormation Managed Resource
```

---

# Resource Replacement

One of the most important Change Set concepts.

Some modifications require:

```text
In-Place Update
```

Others require:

```text
Delete Resource
Create New Resource
```

This is called Replacement.

---

# Replacement Values

CloudFormation displays:

| Value       | Meaning           |
| ----------- | ----------------- |
| True        | Resource replaced |
| False       | Resource updated  |
| Conditional | Depends on change |

---

# Example: No Replacement

```yaml
Tags:
```

change.

Change Set:

```text
Modify
Replacement: False
```

Resource remains intact.

---

# Example: Replacement Required

```yaml
BucketName:
```

change.

Change Set:

```text
Modify
Replacement: True
```

CloudFormation creates a new bucket.

---

# Example Output

```text
WebServer
Action: Modify
Replacement: False

ApplicationBucket
Action: Modify
Replacement: True

Database
Action: Add
Replacement: N/A
```

---

# Executing a Change Set

After review:

AWS Console:

```text
Execute Change Set
```

---

CLI:

```bash
aws cloudformation execute-change-set \
--stack-name production-stack \
--change-set-name update-v1
```

---

# After Execution

```text
Change Set
      │
      ▼
Update Stack
      │
      ▼
Resources Updated
```

Change Set becomes part of stack history.

---

# Deleting a Change Set

Unused Change Sets can be deleted.

CLI:

```bash
aws cloudformation delete-change-set \
--stack-name production-stack \
--change-set-name update-v1
```

---

# Change Set Statuses

## CREATE_PENDING

Change Set creation requested.

---

## CREATE_IN_PROGRESS

CloudFormation analyzing changes.

---

## CREATE_COMPLETE

Change Set ready for review.

---

## FAILED

CloudFormation couldn't create the Change Set.

Possible causes:

```text
Invalid Template
Permission Issues
Resource Errors
```

---

# Example Deployment Workflow

Without Change Sets:

```text
Template
    │
    ▼
Update Stack
```

Risky.

---

With Change Sets:

```text
Template
    │
    ▼
Create Change Set
    │
    ▼
Review
    │
    ▼
Approve
    │
    ▼
Execute
```

Safer.

---

# CI/CD Integration

Common Pipeline:

```text
Git Push
    │
    ▼
Build
    │
    ▼
Create Change Set
    │
    ▼
Approval
    │
    ▼
Execute
```

Widely used in enterprise environments.

---

# Production Deployment Pattern

```text
Developer
    │
    ▼
Create Template

    │
    ▼
Create Change Set

    │
    ▼
Architecture Review

    │
    ▼
Approval

    │
    ▼
Execute Change Set
```

Prevents accidental infrastructure damage.

---

# Change Sets vs Direct Updates

| Feature           | Direct Update | Change Set |
| ----------------- | ------------- | ---------- |
| Preview Changes   | ❌             | ✅          |
| Risk Analysis     | ❌             | ✅          |
| Approval Workflow | ❌             | ✅          |
| Production Safe   | ❌             | ✅          |
| CI/CD Friendly    | ⚠️            | ✅          |

---

# Real-World Example

Production Stack:

```text
ALB
EC2
RDS
S3
```

Developer modifies:

```yaml
DBInstanceClass:
  db.t3.medium
```

Change Set shows:

```text
Database

Action:
Modify

Replacement:
False
```

Safe to deploy.

---

Developer changes:

```yaml
DBSubnetGroupName
```

Change Set shows:

```text
Database

Action:
Modify

Replacement:
True
```

Potential downtime.

Review required.

---

# Best Practices

## Always Use Change Sets in Production

Never update critical stacks blindly.

---

## Review Replacement Changes Carefully

Replacement can cause:

* Downtime
* Data Loss
* Resource Recreation

---

## Integrate with Approval Processes

Use Change Sets before production deployments.

---

## Delete Unused Change Sets

Reduces clutter.

---

## Combine with Stack Policies

Protect critical resources.

---

# Common Mistakes

## Ignoring Replacement Warnings

Can cause accidental resource recreation.

---

## Executing Without Review

Defeats the purpose of Change Sets.

---

## Assuming Modify Means No Downtime

Some modifications still require resource replacement.

---

## Skipping Change Sets in Production

High operational risk.

---

# Key Takeaways

* Change Sets provide a preview of infrastructure changes.
* They compare current and proposed stack states.
* Common actions:

  * Add
  * Modify
  * Remove
  * Import
* Replacement status indicates whether resources will be recreated.
* Change Sets improve deployment safety.
* Widely used in enterprise CI/CD pipelines.
* Considered a CloudFormation best practice for production environments.

---

# Interview Questions

### What is a CloudFormation Change Set?

A Change Set is a preview of infrastructure changes before a stack update is executed.

---

### Why are Change Sets important?

They help identify:

* Resource additions
* Modifications
* Deletions
* Replacements

before deployment.

---

### What actions can appear in a Change Set?

* Add
* Modify
* Remove
* Import

---

### What does Replacement: True mean?

CloudFormation will delete and recreate the resource instead of updating it in place.

---

### Can a Change Set modify infrastructure?

No.

A Change Set only previews changes.

Changes occur only after execution.

---

### Which environments should use Change Sets?

Especially:

* Production
* Staging
* Enterprise environments

where deployment risk must be minimized.

---

### What is the CloudFormation equivalent of Terraform Plan?

**Change Sets**.
