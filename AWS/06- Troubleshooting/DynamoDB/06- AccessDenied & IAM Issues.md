# 06 - AccessDenied & IAM Issues

## Overview

One of the most common production issues when working with Amazon DynamoDB is an authorization failure.

Unlike application bugs or performance bottlenecks, IAM-related issues prevent requests from reaching DynamoDB at all.

The most common error is:

```text
AccessDeniedException
```

Although the message appears simple, the root cause can originate from:

- IAM Users
- IAM Roles
- AWS STS
- Cross-account access
- Resource policies
- Organizations SCPs
- Permission boundaries
- KMS encryption
- Incorrect AWS Region
- Incorrect AWS Account

Senior engineers should know how to quickly isolate the exact permission layer causing the denial.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Common authorization failures
- IAM troubleshooting workflow
- Cross-account access
- Role assumption
- Permission boundaries
- Service Control Policies (SCP)
- KMS permission issues
- Production debugging techniques

---

# Authorization Flow

```text
Application

      │

      ▼

AWS Credentials

      │

      ▼

IAM Evaluation

      │

      ▼

Allow?

 ┌─────────────┐
 │             │
 ▼             ▼

YES          NO

 │             │

 ▼             ▼

DynamoDB   AccessDenied
```

---

# Common Exception

```text
AccessDeniedException

User is not authorized to perform:
dynamodb:GetItem
```

This indicates AWS denied the request before DynamoDB executed it.

---

# IAM Policy Evaluation

AWS evaluates permissions in this order:

```text
Authentication

↓

IAM Policy

↓

Permission Boundary

↓

Organizations SCP

↓

Resource Policy

↓

Explicit Deny?

↓

Allow
```

An explicit deny always overrides an allow.

---

# Common Causes

Authorization failures typically result from:

- Missing IAM permission
- Wrong IAM Role
- Wrong AWS Profile
- Wrong AWS Account
- Wrong AWS Region
- Expired temporary credentials
- Permission boundary restrictions
- SCP restrictions
- Missing KMS permissions

---

# Step 1 — Verify Identity

Always determine who is making the request.

CLI:

```bash
aws sts get-caller-identity
```

Example output:

```json
{
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:role/backend-api",
  "UserId": "AIDA..."
}
```

This immediately confirms:

- AWS Account
- IAM User or Role
- Active credentials

---

# Step 2 — Verify Region

Many engineers accidentally connect to the wrong Region.

Current Region:

```bash
aws configure get region
```

Verify:

```text
Application Region

↓

Matches

↓

DynamoDB Table Region
```

---

# Step 3 — Verify Table Exists

Before checking permissions, ensure the table actually exists.

```bash
aws dynamodb describe-table \
    --table-name Orders
```

If the table exists but access is denied, continue investigating IAM.

---

# Required Permissions

Typical CRUD applications require:

```text
dynamodb:GetItem

dynamodb:PutItem

dynamodb:UpdateItem

dynamodb:DeleteItem

dynamodb:Query

dynamodb:Scan
```

Administrative tasks require additional permissions.

---

# Example IAM Policy

```json
{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Effect":"Allow",
            "Action":[
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query"
            ],
            "Resource":"arn:aws:dynamodb:us-east-1:123456789012:table/Orders"
        }
    ]
}
```

Follow the principle of least privilege.

---

# IAM Role Issues

Common production architecture:

```text
EC2

↓

IAM Role

↓

Temporary Credentials

↓

DynamoDB
```

If the wrong role is attached:

```text
Application

↓

No Permission

↓

AccessDenied
```

---

# ECS / Lambda Example

```text
Lambda Function

↓

Execution Role

↓

DynamoDB
```

If the execution role lacks DynamoDB permissions, every request fails.

---

# Cross-Account Access

Architecture:

```text
Account A

Application

↓

Assume Role

↓

Account B

↓

DynamoDB
```

Requirements:

- Trust policy
- IAM permissions
- Correct role assumption

Any missing piece results in access denial.

---

# Permission Boundaries

Even if an IAM policy allows access:

```text
Allow

↓

Permission Boundary

↓

Denied
```

Permission boundaries limit the maximum permissions a principal can receive.

---

# Service Control Policies (SCP)

Organizations can block actions globally.

Example:

```text
IAM Policy

↓

Allow

↓

SCP

↓

Explicit Deny
```

The request fails despite the IAM policy.

---

# KMS Encryption Issues

Encrypted DynamoDB tables require access to the KMS key.

Missing permission:

```text
kms:Decrypt

kms:GenerateDataKey
```

may produce access-related errors.

---

# Temporary Credentials

Using STS:

```text
Assume Role

↓

Temporary Credentials

↓

Expiration

↓

AccessDenied
```

Refresh credentials before expiration.

---

# Debugging Workflow

```text
AccessDenied

↓

Get Caller Identity

↓

Verify Account

↓

Verify Region

↓

Verify Role

↓

Review IAM Policy

↓

Permission Boundary

↓

SCP

↓

KMS

↓

Root Cause
```

---

# CloudTrail Investigation

CloudTrail records authorization failures.

Useful information:

- Caller identity
- API name
- Timestamp
- Denied action
- Error code

CloudTrail is often the fastest way to identify why a request was rejected.

---

# Production Scenario

Application deployed successfully.

Every request fails.

Investigation:

```text
Deployment

↓

Wrong IAM Role Attached

↓

AccessDenied
```

Fix:

Attach the correct execution role.

---

# Another Production Example

Developer tests locally.

```text
AWS Profile

↓

Development Account
```

Application:

```text
Production Table
```

Result:

```text
Resource Missing

OR

AccessDenied
```

Always verify the active AWS account before debugging.

---

# Monitoring

Monitor:

- AccessDeniedException count
- CloudTrail events
- Failed API calls
- IAM policy changes
- Role assumption failures

Unexpected increases often indicate deployment or security issues.

---

# Production Architecture

```text
Application

      │

      ▼

IAM Role

      │

      ▼

STS Credentials

      │

      ▼

Policy Evaluation

      │

 ┌────┴────┐

 ▼         ▼

Allow     Deny

 │

 ▼

Amazon DynamoDB
```

---

# Performance Considerations

- IAM evaluation is highly optimized and generally not a performance bottleneck.
- Repeated authorization failures can increase application retries and log volume.
- Cache temporary credentials appropriately instead of repeatedly requesting new ones.
- Monitor IAM changes as part of deployment pipelines.

---

# Best Practices

- Follow the principle of least privilege.
- Use IAM Roles instead of long-lived access keys.
- Verify identity with `aws sts get-caller-identity`.
- Keep execution roles separate for different workloads.
- Enable CloudTrail across all production accounts.
- Review IAM policies during code reviews.
- Rotate credentials regularly.

---

# Common Mistakes

## Using AdministratorAccess Everywhere

This hides permission problems during development and violates security best practices.

---

## Hardcoding AWS Credentials

Applications should use IAM Roles whenever possible.

---

## Ignoring AWS Region

Many authorization investigations end up being simple Region mismatches.

---

## Forgetting KMS Permissions

Access to an encrypted table may require permissions on both DynamoDB and the associated KMS key.

---

## Debugging Without CloudTrail

CloudTrail provides valuable context for authorization failures and should be part of every investigation.

---

# Interview Notes

### What causes `AccessDeniedException`?

The caller lacks permission to perform the requested action, or access is blocked by IAM policies, permission boundaries, SCPs, KMS policies, or incorrect credentials.

---

### What is the first command you run when troubleshooting IAM issues?

```bash
aws sts get-caller-identity
```

It confirms the active AWS account and IAM identity.

---

### What is the difference between an IAM policy and an SCP?

- **IAM Policy:** Grants permissions to users or roles within an account.
- **Service Control Policy (SCP):** Defines the maximum permissions available to accounts in an AWS Organization. An SCP can block actions even if an IAM policy allows them.

---

### Why might an application fail after deployment but work locally?

The deployed environment may be using a different IAM role, AWS account, Region, or execution context than the local environment.

---

### Can an explicit deny be overridden by an allow?

No. In AWS authorization, an explicit deny always takes precedence over any allow statement.

---

# Key Takeaways

- `AccessDeniedException` is usually caused by IAM configuration rather than DynamoDB itself.
- Effective troubleshooting starts by identifying the active AWS identity and verifying the account and Region.
- Authorization decisions may involve multiple layers, including IAM policies, permission boundaries, SCPs, resource policies, and KMS permissions.
- CloudTrail and `aws sts get-caller-identity` are essential tools for diagnosing access issues.
- Senior engineers design secure systems using least-privilege IAM roles while maintaining observability for authorization failures.