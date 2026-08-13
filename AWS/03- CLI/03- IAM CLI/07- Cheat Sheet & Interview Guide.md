# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used AWS IAM CLI commands, policy management, security operations, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used IAM CLI commands
- Manage IAM identities efficiently
- Audit IAM security
- Troubleshoot permission issues
- Follow production IAM workflows
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

IAM is one of the most frequently used AWS services.

Engineers rarely memorize every command.

Instead, they remember:

- Command patterns
- Policy workflows
- Security best practices
- Troubleshooting methodology

This chapter provides a practical reference for daily operations.

---

# Command Syntax

General syntax:

```bash
aws iam <operation> [options]
```

Examples:

```bash
aws iam list-users
```

```bash
aws iam create-role
```

```bash
aws iam attach-role-policy
```

---

# User Management Commands

## List Users

```bash
aws iam list-users
```

---

## Create User

```bash
aws iam create-user \
--user-name backend-admin
```

---

## View User

```bash
aws iam get-user \
--user-name backend-admin
```

---

## Delete User

```bash
aws iam delete-user \
--user-name backend-admin
```

---

# Group Management Commands

## List Groups

```bash
aws iam list-groups
```

---

## Create Group

```bash
aws iam create-group \
--group-name Developers
```

---

## Delete Group

```bash
aws iam delete-group \
--group-name Developers
```

---

## Add User to Group

```bash
aws iam add-user-to-group \
--user-name backend-admin \
--group-name Developers
```

---

## Remove User from Group

```bash
aws iam remove-user-from-group \
--user-name backend-admin \
--group-name Developers
```

---

## View Group Members

```bash
aws iam get-group \
--group-name Developers
```

---

# Role Management Commands

## List Roles

```bash
aws iam list-roles
```

---

## Create Role

```bash
aws iam create-role \
--role-name BackendEC2Role \
--assume-role-policy-document file://trust-policy.json
```

---

## View Role

```bash
aws iam get-role \
--role-name BackendEC2Role
```

---

## Delete Role

```bash
aws iam delete-role \
--role-name BackendEC2Role
```

---

# Policy Management Commands

## List AWS Managed Policies

```bash
aws iam list-policies \
--scope AWS
```

---

## List Customer Managed Policies

```bash
aws iam list-policies \
--scope Local
```

---

## Create Policy

```bash
aws iam create-policy \
--policy-name S3ReadOnly \
--policy-document file://policy.json
```

---

## View Policy

```bash
aws iam get-policy \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

---

## List Policy Versions

```bash
aws iam list-policy-versions \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

---

## Delete Policy

```bash
aws iam delete-policy \
--policy-arn arn:aws:iam::123456789012:policy/S3ReadOnly
```

---

# Attach & Detach Policies

## Attach Policy to User

```bash
aws iam attach-user-policy
```

---

## Attach Policy to Group

```bash
aws iam attach-group-policy
```

---

## Attach Policy to Role

```bash
aws iam attach-role-policy
```

---

## Detach Policy from User

```bash
aws iam detach-user-policy
```

---

## Detach Policy from Group

```bash
aws iam detach-group-policy
```

---

## Detach Policy from Role

```bash
aws iam detach-role-policy
```

---

# Access Key Commands

## List Access Keys

```bash
aws iam list-access-keys
```

---

## Create Access Key

```bash
aws iam create-access-key
```

---

## Disable Access Key

```bash
aws iam update-access-key
```

---

## Delete Access Key

```bash
aws iam delete-access-key
```

---

# Instance Profile Commands

## List Instance Profiles

```bash
aws iam list-instance-profiles
```

---

## Create Instance Profile

```bash
aws iam create-instance-profile
```

---

## Add Role to Instance Profile

```bash
aws iam add-role-to-instance-profile
```

---

# STS Commands

## Verify Current Identity

```bash
aws sts get-caller-identity
```

---

## Assume Role

```bash
aws sts assume-role
```

---

# IAM Identity Center Commands

## Configure SSO

```bash
aws configure sso
```

---

## Login

```bash
aws sso login
```

---

## Logout

```bash
aws sso logout
```

---

# Security Commands

## Password Policy

```bash
aws iam get-account-password-policy
```

---

## Update Password Policy

```bash
aws iam update-account-password-policy
```

---

## Generate Credential Report

```bash
aws iam generate-credential-report
```

---

## Download Credential Report

```bash
aws iam get-credential-report
```

---

## List Access Analyzers

```bash
aws accessanalyzer list-analyzers
```

---

## List Findings

```bash
aws accessanalyzer list-findings
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable verbose debugging |
| `--no-cli-pager` | Disable CLI pager |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| AccessDenied | Missing permission | Review IAM Policies, SCPs, Permission Boundaries |
| UnauthorizedOperation | Missing action permission | Update IAM Policy |
| InvalidClientTokenId | Invalid Access Key | Verify AWS credentials |
| ExpiredToken | Temporary credentials expired | Reauthenticate or assume the role again |
| SignatureDoesNotMatch | Invalid Secret Key or Region | Verify credentials and Region |
| NoSuchEntity | Resource not found | Verify User, Role, Group, or Policy name |
| EntityAlreadyExists | Resource already exists | Use a different name or existing resource |
| DeleteConflict | Resource still has dependencies | Remove policies, keys, or memberships first |

---

# IAM Policy Evaluation

```text
Authentication
      │
      ▼
Explicit Deny
      │
      ▼
Service Control Policy
      │
      ▼
Permission Boundary
      │
      ▼
Identity Policy
      │
      ▼
Resource Policy
      │
      ▼
Allow or Deny
```

Always troubleshoot permissions in this order.

---

# Daily IAM Checklist

Before making IAM changes:

- Verify AWS account.
- Verify current identity.
- Follow Least Privilege.
- Avoid wildcard permissions.
- Prefer IAM Roles.
- Enable MFA.
- Review Permission Boundaries.
- Review SCPs.
- Audit Access Analyzer findings.

---

# Interview Questions

## 1. What is the difference between an IAM User and an IAM Role?

**Answer**

An IAM User is a long-term identity with permanent credentials, while an IAM Role provides temporary credentials that are assumed by trusted users or AWS services.

---

## 2. Why should IAM Roles be preferred over Access Keys?

**Answer**

IAM Roles provide temporary credentials through AWS STS, eliminating long-lived Access Keys and improving security.

---

## 3. What is the Principle of Least Privilege?

**Answer**

Grant only the permissions required to perform a task—nothing more.

---

## 4. What is the difference between AWS Managed Policies and Customer Managed Policies?

**Answer**

AWS Managed Policies are maintained by AWS, while Customer Managed Policies are created and maintained within your AWS account, allowing full customization and version control.

---

## 5. What is an Inline Policy?

**Answer**

An Inline Policy is embedded directly into a single IAM User, Group, or Role and cannot be reused.

---

## 6. What is an Explicit Deny?

**Answer**

An Explicit Deny overrides every Allow statement and always prevents access.

---

## 7. What is a Permission Boundary?

**Answer**

A Permission Boundary defines the maximum permissions an IAM identity can receive, regardless of attached policies.

---

## 8. What is IAM Identity Center?

**Answer**

IAM Identity Center is AWS's centralized identity solution that provides Single Sign-On (SSO), Permission Sets, and temporary credentials across multiple AWS accounts.

---

## 9. What is STS?

**Answer**

AWS Security Token Service (STS) issues temporary credentials that are commonly used by IAM Roles, Identity Center, and AssumeRole operations.

---

## 10. How would you troubleshoot an `AccessDenied` error?

**Answer**

Verify the current identity using `aws sts get-caller-identity`, review IAM Policies, check for Explicit Deny statements, inspect Resource Policies, Service Control Policies (SCPs), and Permission Boundaries, then retry with `--debug` if necessary.

---

# Senior Engineer Tips

Experienced AWS engineers typically:

- Prefer IAM Roles over IAM Users.
- Use IAM Identity Center for workforce authentication.
- Create Customer Managed Policies instead of relying on AWS Managed Policies.
- Review IAM policies regularly.
- Rotate credentials and remove unused Access Keys.
- Enable MFA for all privileged accounts.
- Audit IAM using Credential Reports and IAM Access Analyzer.
- Verify the active AWS account before making changes.
- Avoid wildcard permissions in production.
- Follow the Principle of Least Privilege consistently.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Users | `aws iam list-users` |
| Create User | `aws iam create-user` |
| List Groups | `aws iam list-groups` |
| List Roles | `aws iam list-roles` |
| Create Role | `aws iam create-role` |
| List Policies | `aws iam list-policies` |
| Create Policy | `aws iam create-policy` |
| Attach Policy | `aws iam attach-role-policy` |
| List Access Keys | `aws iam list-access-keys` |
| Verify Identity | `aws sts get-caller-identity` |
| Configure SSO | `aws configure sso` |
| Login with SSO | `aws sso login` |

---

# Final Thoughts

AWS IAM is the security foundation of every AWS environment. Whether you're managing users, assigning roles to EC2 instances, configuring CI/CD pipelines, or securing enterprise access with IAM Identity Center, mastering the IAM CLI enables you to automate identity management while maintaining strong security and compliance.

---
