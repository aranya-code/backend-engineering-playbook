# CloudFormation Stack Lifecycle

## What is a Stack?

A Stack is a collection of AWS resources managed as a single unit by CloudFormation.

When CloudFormation processes a template, it creates a Stack that contains all resources defined in that template.

Example:

```text
Production Stack

├── VPC
├── Subnets
├── EC2 Instances
├── Security Groups
├── Load Balancer
└── RDS Database
```

CloudFormation manages the entire lifecycle of these resources.

---

# What is Stack Lifecycle?

The Stack Lifecycle refers to the various states and transitions a CloudFormation stack goes through during its existence.

```text
Create
   ↓
Update
   ↓
Delete
```

CloudFormation tracks every operation through stack states.

---

# Stack Lifecycle Flow

```text
Template
    │
    ▼
Create Stack
    │
    ▼
CREATE_COMPLETE
    │
    ▼
Update Stack
    │
    ▼
UPDATE_COMPLETE
    │
    ▼
Delete Stack
    │
    ▼
DELETE_COMPLETE
```

---

# Stack Creation

When a stack is created:

CloudFormation:

1. Reads the template
2. Validates syntax
3. Evaluates parameters
4. Evaluates conditions
5. Resolves dependencies
6. Creates resources

---

## Create Stack Workflow

```text
Template
   │
   ▼
Validation
   │
   ▼
Resource Planning
   │
   ▼
Resource Creation
   │
   ▼
Stack Complete
```

---

## AWS CLI Example

```bash
aws cloudformation create-stack \
--stack-name production-stack \
--template-body file://template.yaml
```

---

# Stack States During Creation

## CREATE_IN_PROGRESS

CloudFormation is creating resources.

Example:

```text
VPC Created
Subnet Creating
EC2 Pending
```

Status:

```text
CREATE_IN_PROGRESS
```

---

## CREATE_COMPLETE

All resources successfully created.

Status:

```text
CREATE_COMPLETE
```

Stack is ready for use.

---

## CREATE_FAILED

Resource creation failed.

Status:

```text
CREATE_FAILED
```

Possible causes:

* Invalid AMI
* Invalid IAM Permissions
* Duplicate Bucket Name
* Invalid Parameters

---

# Stack Update

CloudFormation supports updating existing stacks.

Instead of rebuilding infrastructure, CloudFormation compares:

```text
Current State
      vs
Desired State
```

and applies only necessary changes.

---

## Update Workflow

```text
Modify Template
       │
       ▼
Update Stack
       │
       ▼
CloudFormation Diff
       │
       ▼
Apply Changes
```

---

## CLI Example

```bash
aws cloudformation update-stack \
--stack-name production-stack \
--template-body file://template.yaml
```

---

# Stack States During Update

## UPDATE_IN_PROGRESS

CloudFormation is updating resources.

---

## UPDATE_COMPLETE

Update completed successfully.

---

## UPDATE_FAILED

Update failed.

Example:

```text
Invalid Security Group
Resource Dependency Issue
Permission Error
```

---

## UPDATE_ROLLBACK_IN_PROGRESS

CloudFormation is reverting failed changes.

---

## UPDATE_ROLLBACK_COMPLETE

Stack returned to previous working state.

---

# Resource Update Behavior

CloudFormation classifies changes into:

### No Interruption

Resource remains running.

Example:

```yaml
Tags:
```

change.

---

### Some Interruption

Temporary downtime may occur.

Example:

```yaml
InstanceType
```

change.

---

### Replacement Required

Old resource deleted.

New resource created.

Example:

```yaml
BucketName
```

change.

---

# Change Detection

CloudFormation automatically detects:

```text
Added Resources
Modified Resources
Deleted Resources
```

during updates.

Example:

```text
Old Template
 ├── EC2
 └── VPC

New Template
 ├── EC2
 ├── VPC
 └── RDS
```

CloudFormation creates only the RDS resource.

---

# Stack Rollback

Rollback occurs when CloudFormation encounters an error.

Example:

```text
Create VPC
Create Subnet
Create EC2
     ❌
Failure
```

CloudFormation:

```text
Delete EC2
Delete Subnet
Delete VPC
```

returns to original state.

---

# Rollback Workflow

```text
Failure
    │
    ▼
Rollback Triggered
    │
    ▼
Delete Created Resources
    │
    ▼
Previous State Restored
```

---

# Stack Deletion

Deleting a stack removes all associated resources.

CLI:

```bash
aws cloudformation delete-stack \
--stack-name production-stack
```

---

# Delete Workflow

```text
Delete Stack
      │
      ▼
Delete Resources
      │
      ▼
DELETE_COMPLETE
```

---

# Stack States During Deletion

## DELETE_IN_PROGRESS

Resources are being deleted.

---

## DELETE_COMPLETE

Stack successfully removed.

---

## DELETE_FAILED

Some resources could not be deleted.

Example:

```text
Non-empty S3 Bucket
Protected Resource
Dependency Issue
```

---

# Common Stack Statuses

| Status                      | Meaning             |
| --------------------------- | ------------------- |
| CREATE_IN_PROGRESS          | Stack being created |
| CREATE_COMPLETE             | Creation successful |
| CREATE_FAILED               | Creation failed     |
| UPDATE_IN_PROGRESS          | Stack updating      |
| UPDATE_COMPLETE             | Update successful   |
| UPDATE_FAILED               | Update failed       |
| UPDATE_ROLLBACK_IN_PROGRESS | Rolling back update |
| UPDATE_ROLLBACK_COMPLETE    | Rollback successful |
| DELETE_IN_PROGRESS          | Stack deleting      |
| DELETE_COMPLETE             | Stack deleted       |
| DELETE_FAILED               | Deletion failed     |

---

# Viewing Stack Events

CloudFormation records every action.

Console:

```text
CloudFormation
      ↓
Stack
      ↓
Events Tab
```

Example:

```text
CREATE_IN_PROGRESS
CREATE_COMPLETE
UPDATE_IN_PROGRESS
UPDATE_COMPLETE
```

Useful for troubleshooting.

---

# Viewing Stack Resources

Console:

```text
CloudFormation
      ↓
Stack
      ↓
Resources Tab
```

Shows:

* Resource IDs
* Status
* Physical IDs
* Resource Types

---

# Viewing Stack Outputs

Console:

```text
CloudFormation
      ↓
Stack
      ↓
Outputs Tab
```

Displays exported values.

Example:

```text
VpcId
BucketName
LoadBalancerDNS
```

---

# Nested Stack Lifecycle

Parent Stack:

```text
Application Stack
```

Child Stack:

```text
Network Stack
Database Stack
Security Stack
```

Lifecycle changes propagate automatically.

---

# Drift Detection

CloudFormation can detect manual changes.

Example:

Template:

```yaml
InstanceType: t3.micro
```

Manual Console Change:

```yaml
InstanceType: t3.large
```

Drift Detection identifies the mismatch.

---

## Drift Workflow

```text
CloudFormation Template
          │
          ▼
Actual Resource
          │
          ▼
Compare
          │
          ▼
Drift Report
```

---

# Best Practices

## Use Change Sets Before Updates

Review changes before deployment.

---

## Avoid Manual Resource Changes

Manual changes cause drift.

---

## Use Stack Policies

Protect critical resources.

---

## Enable Rollback

Provides automatic recovery.

---

## Monitor Stack Events

Always check:

```text
Events Tab
```

when troubleshooting failures.

---

# Common Mistakes

## Manual Resource Modification

Creates configuration drift.

---

## Ignoring Rollback Messages

Rollback events often contain the root cause.

---

## Deleting Shared Resources

Cross-stack dependencies may fail.

---

## Updating Production Directly

Use Change Sets first.

---

# Real-World Example

Production Deployment:

```text
Network Stack
    │
    ├── VPC
    ├── Subnets
    └── Route Tables

Application Stack
    │
    ├── ALB
    ├── EC2
    └── Auto Scaling

Database Stack
    │
    └── RDS
```

Each stack has its own lifecycle.

Updates occur independently.

---

# Key Takeaways

* A Stack is a collection of AWS resources managed by CloudFormation.
* Stack lifecycle includes:

  * Create
  * Update
  * Rollback
  * Delete
* CloudFormation tracks operations using Stack Statuses.
* Failed operations trigger Rollbacks automatically.
* Drift Detection identifies manual changes.
* Stack Events are the primary troubleshooting tool.
* Understanding Stack Statuses is critical for AWS interviews and production environments.

---

# Interview Questions

### What is a CloudFormation Stack?

A Stack is a collection of AWS resources managed as a single unit by CloudFormation.

---

### What happens during stack creation?

CloudFormation:

1. Validates the template
2. Resolves dependencies
3. Creates resources
4. Tracks status

---

### What is CREATE_COMPLETE?

All resources were created successfully.

---

### What is UPDATE_ROLLBACK_COMPLETE?

A stack update failed and CloudFormation successfully restored the previous state.

---

### What causes DELETE_FAILED?

Common causes:

* Non-empty S3 buckets
* Dependency conflicts
* Permission issues

---

### What is Drift Detection?

A feature that compares deployed resources against the CloudFormation template and identifies manual changes.

---

### Which Stack Statuses are most important for troubleshooting?

* CREATE_FAILED
* UPDATE_FAILED
* UPDATE_ROLLBACK_COMPLETE
* DELETE_FAILED
