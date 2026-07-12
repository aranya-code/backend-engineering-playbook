# Change Sets, Drift Detection & StackSets

> Learn how to safely preview infrastructure changes, detect configuration drift, and deploy CloudFormation stacks across multiple AWS accounts and Regions using the AWS CLI. This chapter covers Change Sets, Drift Detection, StackSets, enterprise deployment strategies, and production best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand CloudFormation Change Sets
- Preview infrastructure updates before deployment
- Execute Change Sets safely
- Detect configuration drift
- Understand StackSets
- Deploy infrastructure across multiple AWS accounts
- Deploy infrastructure across multiple AWS Regions
- Apply enterprise deployment strategies

---

# Why Change Sets?

Updating production infrastructure blindly is risky.

Instead of:

```text
Update Stack

↓

Hope Everything Works
```

Use:

```text
Create Change Set

↓

Review Changes

↓

Execute

↓

Infrastructure Updated
```

Change Sets provide a preview of changes before deployment.

---

# Change Set Workflow

```text
Template

↓

Create Change Set

↓

Review Changes

↓

Approve

↓

Execute

↓

Update Stack
```

This reduces deployment risks.

---

# What is a Change Set?

A Change Set is a preview of how CloudFormation will modify your infrastructure.

It identifies:

- Resources to be created
- Resources to be modified
- Resources to be replaced
- Resources to be deleted

No infrastructure changes occur until the Change Set is executed.

---

# Create a Change Set

```bash
aws cloudformation create-change-set \
--stack-name backend-production \
--change-set-name update-v2 \
--template-body file://template.yaml
```

CloudFormation analyzes the template without applying changes.

---

# Create Change Set with Parameters

```bash
aws cloudformation create-change-set \
--stack-name backend-production \
--change-set-name production-update \
--template-body file://template.yaml \
--parameters \
ParameterKey=InstanceType,ParameterValue=t3.large
```

---

# Wait for Change Set Creation

```bash
aws cloudformation wait change-set-create-complete \
--stack-name backend-production \
--change-set-name update-v2
```

---

# List Change Sets

```bash
aws cloudformation list-change-sets \
--stack-name backend-production
```

Returns:

- Change Set Name
- Status
- Creation Time

---

# Describe a Change Set

```bash
aws cloudformation describe-change-set \
--stack-name backend-production \
--change-set-name update-v2
```

Returns:

- Resource Changes
- Replacement Status
- Parameters
- Capabilities

---

# Understanding Change Actions

Possible actions include:

```text
Add

Modify

Remove

Import

Dynamic
```

Each resource change is classified accordingly.

---

# Replacement Behavior

Some updates require resource replacement.

Example:

```text
Modify EC2 Instance

↓

Replacement Required

↓

New Instance Created

↓

Old Instance Deleted
```

Always review replacement operations carefully.

---

# Execute a Change Set

```bash
aws cloudformation execute-change-set \
--stack-name backend-production \
--change-set-name update-v2
```

CloudFormation begins updating the stack.

---

# Delete a Change Set

Unused Change Sets can be removed.

```bash
aws cloudformation delete-change-set \
--stack-name backend-production \
--change-set-name update-v2
```

---

# Why Drift Detection?

CloudFormation expects infrastructure to remain consistent with its template.

Example:

```text
CloudFormation

↓

EC2 Instance

↓

Manual Console Change

↓

Configuration Drift
```

Drift Detection identifies these differences.

---

# Drift Detection Workflow

```text
Template

↓

Running Resources

↓

Compare

↓

Drift Report
```

---

# Start Drift Detection

```bash
aws cloudformation detect-stack-drift \
--stack-name backend-production
```

Returns:

```text
StackDriftDetectionId
```

---

# Check Drift Status

```bash
aws cloudformation describe-stack-drift-detection-status \
--stack-drift-detection-id drift-id
```

Possible statuses:

- DETECTION_IN_PROGRESS
- DETECTION_COMPLETE
- DETECTION_FAILED

---

# View Drift Results

```bash
aws cloudformation describe-stack-resource-drifts \
--stack-name backend-production
```

Returns:

- Resource
- Drift Status
- Expected Configuration
- Actual Configuration

---

# Drift Status Values

Possible results:

```text
IN_SYNC

MODIFIED

DELETED

NOT_CHECKED
```

Production environments should remain **IN_SYNC**.

---

# Understanding StackSets

StackSets deploy CloudFormation stacks across:

- Multiple AWS Accounts
- Multiple AWS Regions

Instead of deploying individually:

```text
Account A

Account B

Account C
```

Deploy once:

```text
StackSet

↓

All Accounts
```

---

# StackSet Architecture

```text
StackSet

│

├── Account A

├── Account B

├── Account C

└── Account D
```

Each account receives its own CloudFormation Stack.

---

# Enterprise Architecture

```text
AWS Organizations

↓

StackSet

↓

Multiple Accounts

↓

Multiple Regions

↓

CloudFormation Stacks
```

Used extensively in enterprise environments.

---

# Create a StackSet

```bash
aws cloudformation create-stack-set \
--stack-set-name security-baseline \
--template-body file://template.yaml
```

---

# List StackSets

```bash
aws cloudformation list-stack-sets
```

---

# Describe a StackSet

```bash
aws cloudformation describe-stack-set \
--stack-set-name security-baseline
```

---

# Create Stack Instances

Deploy the StackSet.

```bash
aws cloudformation create-stack-instances \
--stack-set-name security-baseline \
--accounts 111111111111 \
--regions ap-south-1
```

Multiple accounts and Regions may be specified.

---

# List Stack Instances

```bash
aws cloudformation list-stack-instances \
--stack-set-name security-baseline
```

---

# Delete Stack Instances

```bash
aws cloudformation delete-stack-instances \
--stack-set-name security-baseline \
--accounts 111111111111 \
--regions ap-south-1 \
--retain-stacks
```

---

# Delete a StackSet

```bash
aws cloudformation delete-stack-set \
--stack-set-name security-baseline
```

Delete all Stack Instances before deleting the StackSet itself.

---

# Cross-Account Deployment

Typical workflow:

```text
CloudFormation

↓

StackSet

↓

AWS Organizations

↓

Member Accounts

↓

Resources Created
```

Ideal for deploying:

- IAM Roles
- CloudTrail
- AWS Config
- Security Baselines
- Networking

---

# Multi-Region Deployment

Example:

```text
StackSet

↓

ap-south-1

↓

eu-west-1

↓

us-east-1

↓

us-west-2
```

Ensures consistent infrastructure across Regions.

---

# Common Errors

## ChangeSetNotFound

Verify:

```bash
aws cloudformation list-change-sets \
--stack-name backend-production
```

---

## Change Set Creation Failed

Possible causes:

- Invalid template
- Invalid parameters
- Missing IAM capability

Review:

```bash
aws cloudformation describe-change-set
```

---

## Drift Detection Failed

Possible causes:

- Deleted resources
- Unsupported resource type
- Permission issues

Review stack events and IAM permissions.

---

## StackSet Operation Failed

Verify:

- IAM permissions
- AWS Organizations
- Target accounts
- Target Regions

---

# Production Best Practices

- Always use Change Sets before production updates.
- Review replacement operations carefully.
- Run Drift Detection regularly.
- Never modify CloudFormation-managed resources manually.
- Use StackSets for enterprise deployments.
- Integrate Change Sets into CI/CD pipelines.
- Validate templates before creating Change Sets.
- Tag StackSets consistently.

---

# Real-World Workflow

Enterprise deployment.

```text
Developer

↓

Git

↓

CI/CD Pipeline

↓

Validate Template

↓

Create Change Set

↓

Review

↓

Execute

↓

Run Drift Detection

↓

Deploy StackSet

↓

Production
```

---

# Architecture Note

```text
CloudFormation Template
          │
          ▼
      Change Set
          │
          ▼
     CloudFormation
          │
          ├── Stack
          ├── Drift Detection
          └── StackSet
                 │
                 ▼
     Multiple Accounts
                 │
                 ▼
      Multiple Regions
```

CloudFormation enables controlled, repeatable, and enterprise-scale infrastructure deployments.

---

# Interview Note

### Question

**What is the difference between a Change Set and a StackSet?**

### Answer

A **Change Set** previews the changes that CloudFormation will make to an existing stack before they are applied. It is primarily used to safely review updates and understand the impact on resources. A **StackSet**, on the other hand, is used to deploy and manage the same CloudFormation stack across multiple AWS accounts and Regions, making it ideal for enterprise environments that require consistent infrastructure at scale.

---

# Key Takeaways

- Change Sets allow safe review of infrastructure changes before deployment.
- Execute Change Sets only after reviewing resource modifications and replacements.
- Drift Detection identifies manual changes made outside CloudFormation.
- StackSets enable centralized deployment across multiple AWS accounts and Regions.
- Enterprise deployments typically combine AWS Organizations with StackSets.
- Avoid manual modifications to CloudFormation-managed resources.
- Incorporate Change Sets and Drift Detection into CI/CD workflows.

---
