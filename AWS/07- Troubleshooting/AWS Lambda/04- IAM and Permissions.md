# 04- IAM and Permissions

# Overview

Identity and Access Management (IAM) is one of the most common causes of AWS Lambda failures. Most production incidents involving Lambda are not caused by bugs in the application code but by incorrect IAM policies, missing permissions, invalid trust relationships, or resource policies.

Understanding how Lambda interacts with IAM is essential for building secure, reliable, and production-ready serverless applications.

This chapter covers common IAM and permission issues, how to troubleshoot them, and the best practices followed by experienced backend engineers.

---

# Lambda Security Model

Every Lambda function executes using an IAM Execution Role.

```
Lambda Function

↓

Execution Role

↓

IAM Policy

↓

AWS Resource
```

The execution role determines **what the Lambda function can do**.

---

# Permission Flow

A typical permission flow looks like:

```
API Gateway

↓

Lambda

↓

Execution Role

↓

S3

↓

DynamoDB

↓

Secrets Manager
```

Every AWS API call is authorized using IAM.

---

# Types of Permissions

Lambda uses three primary permission models.

| Permission | Purpose |
|------------|---------|
| Execution Role | Lambda accesses AWS resources |
| Resource Policy | Other services invoke Lambda |
| Identity Policy | User or application invokes Lambda |

Understanding the difference is critical.

---

# Problem: AccessDeniedException

Example

```
AccessDeniedException
```

One of the most common Lambda errors.

---

## Possible Causes

- Missing IAM permission
- Incorrect Resource ARN
- Wrong AWS Region
- Explicit Deny
- SCP restriction

---

## Investigation

Review

```
CloudWatch Logs

↓

IAM Policy

↓

CloudTrail

↓

AWS Resource
```

---

## Resolution

Grant only the required permissions.

Example

Good

```json
{
    "Action": [
        "s3:GetObject"
    ]
}
```

Bad

```json
{
    "Action": "*"
}
```

---

# Problem: Lambda Cannot Read S3

Architecture

```
Lambda

↓

S3

↓

Access Denied
```

---

## Required Permission

```json
s3:GetObject
```

Also verify:

- Bucket Policy
- Object Ownership
- KMS permissions

---

# Problem: Lambda Cannot Write to DynamoDB

Required permission

```json
dynamodb:PutItem
```

Depending on workload:

```
PutItem

UpdateItem

DeleteItem

Query

Scan
```

Grant only necessary actions.

---

# Problem: Lambda Cannot Publish to SNS

Required permission

```json
sns:Publish
```

Common mistake

Correct Topic ARN not specified.

---

# Problem: Lambda Cannot Send Messages to SQS

Required permission

```json
sqs:SendMessage
```

Verify

```
Queue ARN

↓

IAM Policy

↓

Queue Policy
```

---

# Problem: Lambda Cannot Read Secrets

Example

```
AccessDeniedException
```

Required permission

```json
secretsmanager:GetSecretValue
```

Also verify

- Secret ARN
- Region
- KMS permissions

---

# Problem: KMS Access Denied

Example

```
kms:Decrypt Access Denied
```

Root Cause

Lambda can access the encrypted resource but not the encryption key.

Required permission

```json
kms:Decrypt
```

---

# Problem: Unable to Assume Role

Example

```
The role defined for the function cannot be assumed.
```

---

## Root Cause

Incorrect Trust Policy.

Correct trust relationship

```json
{
    "Principal": {
        "Service": "lambda.amazonaws.com"
    }
}
```

---

# Execution Role vs Resource Policy

Execution Role

```
Lambda

↓

Access Resources
```

Resource Policy

```
API Gateway

↓

Invoke Lambda
```

These permissions are independent.

---

# Problem: API Gateway Cannot Invoke Lambda

Possible error

```
Execution failed due to configuration error
```

Required principal

```
apigateway.amazonaws.com
```

Lambda Resource Policy must allow invocation.

---

# Problem: EventBridge Cannot Invoke Lambda

Verify

- EventBridge Rule
- Lambda Resource Policy
- Target ARN

Architecture

```
EventBridge

↓

Lambda
```

---

# Problem: Cross-Account Access

Architecture

```
Account A

↓

Lambda

↓

Assume Role

↓

Account B
```

Instead of sharing credentials:

- Create IAM Role
- Configure Trust Policy
- Use STS AssumeRole

---

# Problem: Explicit Deny

IAM evaluation order

```
Allow

↓

Explicit Deny

↓

Request Denied
```

Explicit Deny always wins.

---

# Problem: SCP Blocking Requests

Organizations Service Control Policies (SCPs) override IAM permissions.

Example

```
IAM Allow

↓

SCP Deny

↓

Request Fails
```

Always verify SCPs in enterprise environments.

---

# Problem: Wrong Resource ARN

Example

```
arn:aws:s3:::bucket
```

instead of

```
arn:aws:s3:::bucket/*
```

Small ARN mistakes frequently cause permission failures.

---

# IAM Policy Simulator

AWS provides an IAM Policy Simulator.

Useful for testing

```
IAM Policy

↓

Action

↓

Resource

↓

Result
```

Use it before modifying production policies.

---

# CloudTrail

CloudTrail records authorization failures.

Example

```
AccessDenied

↓

CloudTrail Event

↓

IAM Principal

↓

Action

↓

Reason
```

CloudTrail is invaluable for debugging permission issues.

---

# Least Privilege Principle

Instead of

```json
Action: "*"
```

Grant only

```json
s3:GetObject

dynamodb:PutItem

sns:Publish
```

Minimal permissions reduce security risk.

---

# Common Permission Mistakes

❌ AdministratorAccess

❌ Wildcard Resource

❌ Wildcard Action

❌ Hardcoded Credentials

❌ Long-lived Access Keys

❌ Shared IAM Roles

---

# Production Checklist

Before deployment:

- [ ] Execution Role reviewed
- [ ] Trust Policy verified
- [ ] Resource Policies configured
- [ ] Least Privilege applied
- [ ] Secrets Manager permissions verified
- [ ] KMS permissions tested
- [ ] CloudTrail enabled
- [ ] IAM Policy Simulator used
- [ ] No wildcard permissions
- [ ] Cross-account roles verified

---

# Troubleshooting Workflow

```
Permission Error

↓

CloudWatch Logs

↓

CloudTrail

↓

Execution Role

↓

Resource Policy

↓

Trust Policy

↓

Fix

↓

Retest
```

---

# Best Practices

✅ Follow the Principle of Least Privilege.

✅ Use IAM Roles instead of Access Keys.

✅ Store secrets in AWS Secrets Manager.

✅ Rotate credentials regularly.

✅ Use temporary credentials whenever possible.

✅ Enable CloudTrail for auditing.

✅ Test IAM policies before deployment.

✅ Separate execution roles by application.

---

# Real-World Example

```
Users

↓

API Gateway

↓

Lambda

↓

Execution Role

├── Secrets Manager

├── S3

├── DynamoDB

└── SNS

↓

CloudTrail
```

Every AWS service access is governed by IAM permissions.

---

# Senior Backend Engineering Perspective

Experienced engineers treat IAM as a foundational part of application design rather than an afterthought. Instead of granting broad permissions to "make it work," they design narrowly scoped roles, validate permissions during CI/CD, and continuously audit access using CloudTrail and IAM analysis tools.

Strong IAM practices improve both security and operational reliability by ensuring that applications have exactly the permissions they need—and nothing more.

---

# Key Takeaways

- IAM misconfigurations are among the most common causes of Lambda production failures.
- Execution Roles, Resource Policies, and Trust Policies each serve different purposes and must be configured correctly.
- CloudTrail and the IAM Policy Simulator are essential tools for debugging authorization issues.
- Apply the Principle of Least Privilege to minimize security risks.
- Well-designed IAM policies improve security, maintainability, and production reliability.