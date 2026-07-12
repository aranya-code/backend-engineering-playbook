# IAM Policies

> Learn how IAM Policies control access to AWS resources using the AWS CLI. This chapter covers policy types, JSON policy syntax, policy evaluation logic, permission boundaries, and production best practices for designing secure, least-privilege access.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand IAM Policy types
- Create and manage IAM Policies
- Read and write JSON policy documents
- Understand policy evaluation logic
- Apply least privilege principles
- Manage policy versions
- Use permission boundaries
- Troubleshoot permission issues

---

# What is an IAM Policy?

An IAM Policy is a JSON document that defines **who can do what on which resources under what conditions**.

Policies are attached to:

- Users
- Groups
- Roles

Policies never authenticate users.

They only determine what authenticated identities are allowed to do.

---

# IAM Authorization Model

```text
Authenticated Identity
        │
        ▼
IAM Policy
        │
        ▼
Allow or Deny
        │
        ▼
AWS Resource
```

Every AWS API request passes through policy evaluation.

---

# Types of IAM Policies

AWS supports several policy types.

```text
IAM Policies
│
├── AWS Managed Policies
├── Customer Managed Policies
├── Inline Policies
├── Resource Policies
├── Permission Boundaries
├── SCPs (Organizations)
└── Session Policies
```

The first three are the most commonly used in daily operations.

---

# AWS Managed Policies

AWS provides pre-built policies.

Examples:

- AdministratorAccess
- ReadOnlyAccess
- AmazonS3ReadOnlyAccess
- AmazonEC2ReadOnlyAccess
- AmazonEC2FullAccess

Advantages:

- Maintained by AWS
- Easy to use
- Frequently updated

Disadvantages:

- Often broader than required
- May violate least privilege

---

# List AWS Managed Policies

```bash
aws iam list-policies \
--scope AWS
```

---

# Customer Managed Policies

Customer Managed Policies are created and maintained by your AWS account.

Advantages:

- Full customization
- Easier auditing
- Reusable
- Version controlled

Production environments typically rely on Customer Managed Policies.

---

# List Customer Managed Policies

```bash
aws iam list-policies \
--scope Local
```

---

# Inline Policies

Inline Policies are embedded directly inside a single:

- User
- Group
- Role

Unlike managed policies:

- Cannot be reused
- Deleted automatically with the identity

They are generally used only for special cases.

---

# IAM Policy Structure

Every IAM Policy contains:

```text
Policy
 │
 ├── Version
 ├── Statement
 │      ├── Effect
 │      ├── Action
 │      ├── Resource
 │      └── Condition (Optional)
```

---

# Basic IAM Policy

```json
{
    "Version":"2012-10-17",
    "Statement":[
        {
            "Effect":"Allow",
            "Action":"s3:ListBucket",
            "Resource":"arn:aws:s3:::company-backups"
        }
    ]
}
```

---

# Understanding Version

Example:

```json
"Version":"2012-10-17"
```

This refers to the IAM policy language version.

It does **not** represent your policy version.

---

# Understanding Effect

Possible values:

```text
Allow

Deny
```

Explicit Deny always overrides Allow.

---

# Understanding Action

Actions define **what** can be performed.

Examples:

```text
ec2:StartInstances

ec2:StopInstances

s3:GetObject

lambda:InvokeFunction

cloudformation:CreateStack
```

Wildcards are supported.

Example:

```text
ec2:*
```

---

# Understanding Resource

Resources define **where** actions are allowed.

Example:

```text
arn:aws:s3:::company-backups
```

Or

```text
*
```

Avoid using `*` in production whenever possible.

---

# Understanding Conditions

Conditions provide additional restrictions.

Example:

```json
"Condition":{
    "IpAddress":{
        "aws:SourceIp":"203.0.113.0/24"
    }
}
```

Common condition keys include:

- IP address
- MFA
- Date
- Time
- AWS Region
- Tags

Conditions enable fine-grained access control.

---

# Creating a Customer Managed Policy

Store the JSON document locally.

Example:

```bash
policy.json
```

Create the policy:

```bash
aws iam create-policy \
--policy-name S3ReadOnly \
--policy-document file://policy.json
```

---

# View a Policy

```bash
aws iam get-policy \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

---

# View Policy Version

```bash
aws iam get-policy-version \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly \
--version-id v1
```

---

# List Policy Versions

```bash
aws iam list-policy-versions \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

IAM supports up to five policy versions.

---

# Delete a Policy

```bash
aws iam delete-policy \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

Detach the policy from all identities before deleting it.

---

# Attaching Policies

Attach to a User:

```bash
aws iam attach-user-policy \
--user-name backend-admin \
--policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

---

Attach to a Group:

```bash
aws iam attach-group-policy \
--group-name Developers \
--policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

---

Attach to a Role:

```bash
aws iam attach-role-policy \
--role-name BackendEC2Role \
--policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

---

# Detaching Policies

Detach from a User:

```bash
aws iam detach-user-policy \
--user-name backend-admin \
--policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

---

Detach from a Role:

```bash
aws iam detach-role-policy \
--role-name BackendEC2Role \
--policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

---

# IAM Policy Evaluation Logic

AWS evaluates policies in this order.

```text
Authentication
      │
      ▼
Explicit Deny?
      │
     Yes
      │
      ▼
Access Denied
      │
     No
      ▼
Explicit Allow?
      │
     Yes
      ▼
Access Allowed
      │
     No
      ▼
Implicit Deny
```

Understanding this evaluation process is critical for troubleshooting permission issues.

---

# Explicit vs Implicit Deny

If no policy allows an action:

```text
Implicit Deny
```

If a policy explicitly denies an action:

```text
Explicit Deny
```

Explicit Deny always takes precedence.

---

# Permission Boundaries

Permission Boundaries define the **maximum permissions** an identity can receive.

```text
User

↓

Attached Policies

↓

Permission Boundary

↓

Effective Permissions
```

Even if a policy allows an action, the Permission Boundary can prevent it.

---

# Least Privilege Principle

Instead of:

```text
s3:*
```

Prefer:

```text
s3:GetObject

s3:PutObject
```

Grant only the permissions required to perform a task.

---

# Common Errors

## AccessDenied

Possible causes:

- Missing IAM Policy
- Explicit Deny
- SCP restriction
- Permission Boundary
- Resource Policy

---

## MalformedPolicyDocument

Cause:

Invalid JSON syntax.

Validate the JSON before uploading.

---

## LimitExceeded

Cause:

Policy or version limits reached.

Remove unused policy versions.

---

# Production Best Practices

- Prefer Customer Managed Policies.
- Avoid Inline Policies unless necessary.
- Follow the Principle of Least Privilege.
- Avoid wildcard (`*`) permissions whenever possible.
- Review policies regularly.
- Use descriptive policy names.
- Remove unused permissions.
- Document policy purpose and ownership.

---

# Real-World Workflow

Grant S3 read-only access.

```text
Create Policy
      │
      ▼
Validate JSON
      │
      ▼
Create Customer Managed Policy
      │
      ▼
Attach to Group
      │
      ▼
Users Receive Permissions
```

---

# Architecture Note

```text
IAM Identity
      │
      ▼
Attached Policies
      │
      ▼
Policy Evaluation
      │
      ├── Explicit Deny
      ├── Explicit Allow
      └── Implicit Deny
      │
      ▼
AWS Resource
```

Policy evaluation occurs for every authenticated AWS API request.

---

# Interview Note

### Question

**What is the difference between AWS Managed Policies, Customer Managed Policies, and Inline Policies?**

### Answer

**AWS Managed Policies** are created and maintained by AWS, making them easy to use but often broader than required. **Customer Managed Policies** are created and maintained within your AWS account, allowing full customization, versioning, and reuse across multiple identities. **Inline Policies** are embedded directly into a single user, group, or role and cannot be reused. Production environments typically favor Customer Managed Policies because they provide better control, auditing, and adherence to the Principle of Least Privilege.

---

# Key Takeaways

- IAM Policies define permissions, not identities.
- Customer Managed Policies are recommended for production.
- Policies are written in JSON.
- Every policy contains Version, Statement, Effect, Action, and Resource.
- Explicit Deny overrides Allow.
- Permission Boundaries restrict the maximum permissions available.
- Follow the Principle of Least Privilege when designing IAM policies.

---
