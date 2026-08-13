# Troubleshooting & Best Practices

> Learn how to troubleshoot common AWS CloudFormation issues using the AWS CLI and apply production-ready best practices for Infrastructure as Code (IaC). This chapter covers stack failures, rollback recovery, template debugging, deployment strategies, and operational recommendations.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot CloudFormation deployment failures
- Investigate stack rollback issues
- Debug template errors
- Recover failed stacks
- Diagnose dependency problems
- Audit CloudFormation deployments
- Apply production deployment best practices

---

# Why Troubleshooting CloudFormation Matters

CloudFormation automates infrastructure deployment.

When deployments fail, the root cause is usually:

- Invalid template
- Incorrect IAM permissions
- Missing dependencies
- Invalid resource properties
- Service quotas
- Existing resources
- Incorrect parameters

A structured troubleshooting process helps identify and resolve issues quickly.

---

# CloudFormation Troubleshooting Workflow

Whenever a deployment fails:

```text
Validate Template
        │
        ▼
Verify Parameters
        │
        ▼
Review IAM Permissions
        │
        ▼
Review Stack Events
        │
        ▼
Review Resource Errors
        │
        ▼
Fix Template
        │
        ▼
Deploy Again
```

Always begin with the stack events.

---

# Validate the Template

Before deployment:

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

Validation checks:

- JSON syntax
- YAML syntax
- Required sections
- Template format

It does **not** verify business logic.

---

# Verify Stack Status

```bash
aws cloudformation describe-stacks \
--stack-name backend-production
```

Common statuses:

```text
CREATE_COMPLETE

UPDATE_COMPLETE

CREATE_FAILED

ROLLBACK_COMPLETE

UPDATE_ROLLBACK_COMPLETE
```

---

# Review Stack Events

The first troubleshooting step:

```bash
aws cloudformation describe-stack-events \
--stack-name backend-production
```

Events contain:

- Failed resource
- Error message
- Timestamp
- Status

Read from the newest event upward.

---

# Error: ValidationError

Example:

```text
Template validation error
```

Possible causes:

- Invalid YAML
- Invalid JSON
- Missing Parameters
- Unsupported resource

Validate:

```bash
aws cloudformation validate-template
```

---

# Error: AlreadyExistsException

Example:

```text
Resource already exists
```

Possible causes:

- S3 Bucket name already exists
- IAM Role already exists
- Log Group already exists

Use unique names or import existing resources.

---

# Error: InsufficientCapabilitiesException

Occurs when templates create:

- IAM Users
- IAM Roles
- IAM Policies

Deploy using:

```bash
aws cloudformation create-stack \
--capabilities CAPABILITY_NAMED_IAM
```

---

# Error: AccessDenied

Possible causes:

- Missing IAM permissions
- SCP restrictions
- Permission Boundary
- Missing service permissions

Verify:

```bash
aws sts get-caller-identity
```

---

# Error: CREATE_FAILED

Example:

```text
CREATE_FAILED
```

Possible causes:

- Invalid parameter
- Missing dependency
- Existing resource
- Invalid property

Review stack events.

---

# Error: UPDATE_ROLLBACK_FAILED

Example:

```text
UPDATE_ROLLBACK_FAILED
```

CloudFormation could not restore the previous infrastructure.

Continue rollback:

```bash
aws cloudformation continue-update-rollback \
--stack-name backend-production
```

---

# Error: DELETE_FAILED

Possible causes:

- S3 bucket contains objects
- Security Group still attached
- EBS Volume attached
- Resource dependency exists

CloudFormation cannot delete resources with active dependencies.

---

# Error: No Updates Are To Be Performed

Example:

```text
No updates are to be performed.
```

CloudFormation detected no infrastructure changes.

This is informational, not an error.

---

# Parameter Problems

Deployment fails?

Verify:

- Parameter names
- Parameter types
- Allowed values
- Default values

Example:

```bash
aws cloudformation create-stack \
--parameters \
ParameterKey=Environment,ParameterValue=Production
```

---

# IAM Permission Problems

Verify current identity:

```bash
aws sts get-caller-identity
```

Common missing permissions:

- iam:PassRole
- ec2:RunInstances
- s3:CreateBucket
- lambda:CreateFunction
- cloudformation:CreateStack

---

# Dependency Problems

Example:

```text
Security Group

↓

VPC

↓

VPC Deleted

↓

Stack Failure
```

Resources must be created and deleted in dependency order.

---

# Rollback Workflow

```text
Deployment

↓

Failure

↓

Rollback

↓

Previous State Restored
```

Rollback protects existing infrastructure from partial deployments.

---

# Continue Rollback

If rollback stops:

```bash
aws cloudformation continue-update-rollback \
--stack-name backend-production
```

Useful after manually resolving resource issues.

---

# Detect Infrastructure Drift

```bash
aws cloudformation detect-stack-drift \
--stack-name backend-production
```

Followed by:

```bash
aws cloudformation describe-stack-resource-drifts \
--stack-name backend-production
```

Run drift detection regularly.

---

# Debug Using Stack Events

Typical investigation:

```text
Deployment Failed

↓

Describe Stack Events

↓

Locate First Failed Resource

↓

Read Failure Reason

↓

Fix Template

↓

Deploy Again
```

Never guess the cause.

---

# CloudFormation Limits

Common limits include:

- Number of resources per template
- Number of outputs
- Number of parameters
- Stack size
- Template size

Review AWS service quotas when large deployments fail.

---

# Production Deployment Checklist

Before deployment:

- □ Validate template
- □ Verify AWS account
- □ Verify Region
- □ Verify Parameters
- □ Verify IAM permissions
- □ Review Change Set
- □ Confirm resource names
- □ Verify quotas

---

# Production Best Practices

## Validate Templates

Always validate before deployment.

```bash
aws cloudformation validate-template
```

---

## Use Change Sets

Never deploy directly to production.

Preferred workflow:

```text
Template

↓

Change Set

↓

Review

↓

Execute
```

---

## Avoid Manual Changes

Never manually modify CloudFormation-managed resources.

Otherwise:

```text
Manual Change

↓

Drift

↓

Unexpected Updates
```

---

## Use Nested Stacks

Separate infrastructure into:

- Network
- Security
- Database
- Application

This simplifies maintenance.

---

## Version Control Templates

Store templates in Git.

Benefits:

- History
- Code Review
- Rollback
- Collaboration

---

## Monitor Stack Events

Every deployment should include:

```bash
aws cloudformation describe-stack-events
```

This provides detailed deployment diagnostics.

---

## Protect Critical Resources

Use Stack Policies to prevent accidental updates to:

- Databases
- IAM Roles
- S3 Buckets
- Networking resources

---

# Real-World Workflow

Production deployment.

```text
Developer

↓

Git

↓

CI/CD

↓

Validate Template

↓

Create Change Set

↓

Review

↓

Deploy

↓

Monitor Events

↓

Production
```

---

# Architecture Note

```text
CloudFormation Template
          │
          ▼
Template Validation
          │
          ▼
CloudFormation Engine
          │
          ▼
Stack Events
          │
          ▼
AWS Resources
```

Stack Events provide the most valuable troubleshooting information during deployments.

---

# Interview Note

### Question

**How would you troubleshoot a CloudFormation stack stuck in `CREATE_FAILED`?**

### Answer

I would first review the stack events using `aws cloudformation describe-stack-events` to identify the first resource that failed. Next, I would verify the template syntax with `validate-template`, check parameter values, confirm IAM permissions, and review service-specific errors such as resource quotas or naming conflicts. Once the root cause is corrected, I would redeploy the stack or continue the rollback if necessary.

---

# Key Takeaways

- Stack Events are the primary source for CloudFormation troubleshooting.
- Validate templates before every deployment.
- Use Change Sets to reduce production risk.
- Review IAM permissions when deployments fail.
- Understand rollback behavior and recovery options.
- Detect and eliminate configuration drift.
- Avoid manual changes to CloudFormation-managed resources.
- Keep templates modular, version controlled, and reusable.