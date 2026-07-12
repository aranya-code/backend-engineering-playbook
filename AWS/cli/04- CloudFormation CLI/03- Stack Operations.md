# Stack Operations

> Learn how to manage the complete lifecycle of CloudFormation stacks using the AWS CLI. This chapter covers creating, updating, deleting, rolling back, protecting, importing, exporting, and monitoring CloudFormation stacks in production environments.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create CloudFormation stacks
- Update existing stacks
- Delete stacks safely
- Understand rollback behavior
- Protect stacks using Stack Policies
- Import existing AWS resources
- Export stack values
- Monitor stack events
- Manage production deployments

---

# CloudFormation Stack Lifecycle

Every CloudFormation stack follows a lifecycle.

```text
Template
      │
      ▼
Create Stack
      │
      ▼
Create Resources
      │
      ▼
Update Stack
      │
      ▼
Delete Stack
```

CloudFormation manages every stage automatically.

---

# Stack Status Flow

```text
CREATE_IN_PROGRESS
        │
        ▼
CREATE_COMPLETE
        │
        ▼
UPDATE_IN_PROGRESS
        │
        ▼
UPDATE_COMPLETE
        │
        ▼
DELETE_IN_PROGRESS
        │
        ▼
DELETE_COMPLETE
```

Every stack operation changes the stack status.

---

# Create a Stack

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml
```

CloudFormation creates all resources defined in the template.

---

# Create Stack with Parameters

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml \
--parameters \
ParameterKey=Environment,ParameterValue=Production
```

Parameters make templates reusable across environments.

---

# Create Stack with IAM Resources

Templates that create IAM resources require acknowledgment.

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

Without this capability, stack creation fails.

---

# Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete \
--stack-name backend-production
```

Useful for automation pipelines.

---

# Describe a Stack

```bash
aws cloudformation describe-stacks \
--stack-name backend-production
```

Returns:

- Parameters
- Outputs
- Tags
- Stack Status
- Creation Time

---

# Update a Stack

Modify infrastructure by updating the template.

```bash
aws cloudformation update-stack \
--stack-name backend-production \
--template-body file://template.yaml
```

CloudFormation determines which resources require modification.

---

# Update Stack with Parameters

```bash
aws cloudformation update-stack \
--stack-name backend-production \
--template-body file://template.yaml \
--parameters \
ParameterKey=InstanceType,ParameterValue=t3.medium
```

---

# Wait for Stack Update

```bash
aws cloudformation wait stack-update-complete \
--stack-name backend-production
```

Automation should wait until updates finish successfully.

---

# Delete a Stack

```bash
aws cloudformation delete-stack \
--stack-name backend-production
```

CloudFormation removes all managed resources.

---

# Wait for Deletion

```bash
aws cloudformation wait stack-delete-complete \
--stack-name backend-production
```

---

# Listing Stacks

```bash
aws cloudformation list-stacks
```

Useful for auditing infrastructure.

---

# Listing Stack Resources

```bash
aws cloudformation list-stack-resources \
--stack-name backend-production
```

Displays every managed AWS resource.

---

# Viewing Stack Events

```bash
aws cloudformation describe-stack-events \
--stack-name backend-production
```

Returns:

- Event Time
- Resource
- Status
- Failure Reason

This is the first place to investigate deployment failures.

---

# Stack Rollback

CloudFormation automatically rolls back failed deployments.

Example:

```text
Update Stack

↓

Resource Creation Fails

↓

Rollback Begins

↓

Previous Infrastructure Restored
```

Rollback minimizes the impact of failed deployments.

---

# Rollback Status

Example:

```text
UPDATE_ROLLBACK_IN_PROGRESS
```

Then:

```text
UPDATE_ROLLBACK_COMPLETE
```

Review stack events to identify the root cause.

---

# Continue a Failed Rollback

If rollback is interrupted:

```bash
aws cloudformation continue-update-rollback \
--stack-name backend-production
```

Useful when resolving partially failed updates.

---

# Cancel an Update

```bash
aws cloudformation cancel-update-stack \
--stack-name backend-production
```

Only available while an update is in progress.

---

# Detect Stack Drift

Infrastructure can change outside CloudFormation.

Example:

```text
CloudFormation

↓

EC2 Instance

↓

Manual Console Change

↓

Drift
```

CloudFormation can detect these changes.

---

# Start Drift Detection

```bash
aws cloudformation detect-stack-drift \
--stack-name backend-production
```

Returns a Drift Detection ID.

---

# View Drift Status

```bash
aws cloudformation describe-stack-drift-detection-status \
--stack-drift-detection-id drift-id
```

Possible results:

- DETECTION_IN_PROGRESS
- DETECTION_COMPLETE

---

# Describe Drifted Resources

```bash
aws cloudformation describe-stack-resource-drifts \
--stack-name backend-production
```

Shows resources that differ from the template.

---

# Export Stack Values

Outputs can be exported.

Example:

```yaml
Outputs:

  VpcId:

    Value: !Ref BackendVPC

    Export:

      Name: ProductionVpc
```

Other stacks can reference this export.

---

# List Exports

```bash
aws cloudformation list-exports
```

---

# List Imports

```bash
aws cloudformation list-imports \
--export-name ProductionVpc
```

Useful for identifying stack dependencies.

---

# Import Existing Resources

CloudFormation can adopt existing AWS resources.

Typical workflow:

```text
Existing Resource

↓

Import Template

↓

CloudFormation Stack
```

This allows previously unmanaged infrastructure to become managed by CloudFormation.

---

# Stack Policies

Stack Policies protect critical resources.

Example:

```text
Stack

↓

Policy

↓

Prevent Accidental Updates
```

Often used to protect:

- Databases
- Production S3 Buckets
- Critical IAM Roles

---

# View Stack Policy

```bash
aws cloudformation get-stack-policy \
--stack-name backend-production
```

---

# Set a Stack Policy

```bash
aws cloudformation set-stack-policy \
--stack-name backend-production \
--stack-policy-body file://policy.json
```

---

# Stack Operation Workflow

```text
Write Template
      │
      ▼
Validate
      │
      ▼
Create Stack
      │
      ▼
Monitor Events
      │
      ▼
Update Stack
      │
      ▼
Rollback (if required)
      │
      ▼
Delete Stack
```

---

# Common Errors

## No updates are to be performed

Example:

```text
No updates are to be performed.
```

CloudFormation detected no infrastructure changes.

---

## UPDATE_ROLLBACK_FAILED

Cause:

Rollback failed because a resource could not be restored.

Resolution:

```bash
aws cloudformation continue-update-rollback
```

---

## DELETE_FAILED

Possible causes:

- S3 bucket not empty
- Resource locked
- Dependency exists
- Manual resource changes

Review stack events for details.

---

## ValidationError

Example:

```text
Stack with id does not exist.
```

Verify:

- Stack name
- AWS account
- Region

---

# Production Best Practices

- Validate templates before deployment.
- Use Change Sets before production updates.
- Never modify CloudFormation-managed resources manually.
- Monitor stack events during every deployment.
- Protect critical resources with Stack Policies.
- Enable drift detection periodically.
- Store templates in Git.
- Use descriptive stack names and tags.

---

# Real-World Workflow

Production deployment.

```text
Developer
      │
      ▼
Git Repository
      │
      ▼
CI/CD Pipeline
      │
      ▼
Validate Template
      │
      ▼
Create Change Set
      │
      ▼
Review Changes
      │
      ▼
Execute Update
      │
      ▼
Monitor Events
      │
      ▼
Deployment Complete
```

---

# Architecture Note

```text
CloudFormation Template
          │
          ▼
CloudFormation Stack
          │
          ├── EC2
          ├── VPC
          ├── IAM
          ├── S3
          ├── Lambda
          ├── RDS
          └── CloudWatch
```

The stack becomes the single source of truth for all managed infrastructure.

---

# Interview Note

### Question

**What happens if a CloudFormation stack update fails?**

### Answer

When a stack update fails, CloudFormation automatically initiates a rollback. During rollback, it attempts to restore the infrastructure to its last known stable state by undoing any successful changes made during the failed update. If rollback itself encounters an issue, the stack enters the `UPDATE_ROLLBACK_FAILED` state, requiring manual intervention using commands such as `continue-update-rollback` after resolving the underlying problem.

---

# Key Takeaways

- CloudFormation manages the full lifecycle of infrastructure.
- Stack updates modify only the resources that require changes.
- Failed deployments automatically trigger rollback.
- Stack Events are the primary source for troubleshooting.
- Drift Detection identifies manual infrastructure changes.
- Stack Policies protect critical production resources.
- Infrastructure should always be updated through CloudFormation rather than manual console changes.

---
