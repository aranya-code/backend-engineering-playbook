# Introduction to IAM CLI

> Learn how to manage AWS Identity and Access Management (IAM) using the AWS Command Line Interface (AWS CLI). This chapter introduces IAM concepts, explains how the CLI interacts with IAM resources, and builds the foundation for secure identity and permission management.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand the purpose of AWS IAM.
- Navigate IAM CLI commands.
- Understand IAM resources.
- Differentiate between authentication and authorization.
- List IAM users, groups, roles, and policies.
- Build a strong foundation for secure AWS administration.

---

# Why Learn IAM CLI?

AWS Identity and Access Management (IAM) is the security foundation of every AWS account.

Almost every AWS API request is evaluated against IAM policies before it is allowed.

Backend Engineers, DevOps Engineers, and Cloud Engineers use IAM CLI for:

- User management
- Role management
- Policy management
- Automation
- CI/CD authentication
- Cross-account access
- Security audits
- Compliance

Although IAM can be managed through the AWS Console, production environments rely heavily on the AWS CLI and Infrastructure as Code (IaC).

---

# How AWS CLI Communicates with IAM

IAM commands follow the pattern:

```bash
aws iam <operation>
```

Examples:

```bash
aws iam list-users
```

```bash
aws iam list-roles
```

```bash
aws iam list-groups
```

```bash
aws iam list-policies
```

Every IAM CLI command maps directly to an AWS IAM API.

---

# Understanding IAM Resources

Amazon IAM consists of several resource types.

```text
AWS IAM
│
├── Users
├── Groups
├── Roles
├── Policies
├── Access Keys
├── MFA Devices
├── Instance Profiles
└── Identity Center (SSO)
```

Each resource has dedicated CLI operations.

---

# Authentication vs Authorization

One of the most important IAM concepts.

Authentication answers:

> **Who are you?**

Examples:

- IAM User
- IAM Role
- Federated User
- AWS Identity Center User

Authorization answers:

> **What are you allowed to do?**

Authorization is controlled using IAM Policies.

---

# IAM Evaluation Flow

Every AWS request follows this process.

```text
AWS Request
      │
      ▼
Authentication
      │
      ▼
IAM Policy Evaluation
      │
      ▼
Resource Policy (if applicable)
      │
      ▼
Service Control Policy (SCP)
      │
      ▼
Permission Boundary
      │
      ▼
Allow / Deny
```

Understanding this flow is critical when troubleshooting permissions.

---

# Listing IAM Users

```bash
aws iam list-users
```

Example output:

```json
{
    "Users": [
        {
            "UserName": "backend-admin"
        }
    ]
}
```

---

# Listing IAM Roles

```bash
aws iam list-roles
```

Roles are commonly used by:

- EC2
- Lambda
- ECS
- EKS
- CloudFormation

and should generally be preferred over long-lived IAM users for workloads.

---

# Listing IAM Groups

```bash
aws iam list-groups
```

Groups simplify permission management by assigning policies to multiple users at once.

---

# Listing Customer-Managed Policies

```bash
aws iam list-policies \
--scope Local
```

Returns policies created within your AWS account.

---

# AWS Managed Policies

List AWS-managed policies:

```bash
aws iam list-policies \
--scope AWS
```

These are maintained by AWS and cover common permission sets.

---

# Viewing Your Current Identity

Always verify the active identity before making IAM changes.

```bash
aws sts get-caller-identity
```

Example output:

```json
{
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/backend-admin",
    "UserId": "AIDAXXXXXXXXXXXXX"
}
```

This command is one of the most frequently used during troubleshooting.

---

# Global Options

IAM commands support all AWS CLI global options.

Examples:

```bash
aws iam list-users \
--output table
```

```bash
aws iam list-users \
--profile production
```

```bash
aws iam list-users \
--no-cli-pager
```

---

# Production Tip

Never perform IAM changes until you've verified:

```bash
aws sts get-caller-identity
```

Making permission changes in the wrong AWS account is a common operational mistake.

---

# Architecture Note

```text
Developer
      │
      ▼
AWS CLI
      │
      ▼
IAM API
      │
      ▼
Users
Groups
Roles
Policies
      │
      ▼
AWS Resources
```

IAM acts as the authorization layer for nearly every AWS service.

---

# Interview Note

### Question

**Why is IAM considered one of the most important AWS services?**

### Answer

IAM controls authentication and authorization for AWS resources. Every request to AWS services is evaluated against IAM policies, making IAM the foundation of AWS security. Proper IAM configuration ensures that users, applications, and services receive only the permissions they require, following the Principle of Least Privilege.

---

# Key Takeaways

- IAM controls authentication and authorization across AWS.
- IAM CLI commands use the `aws iam` namespace.
- Users, Groups, Roles, and Policies are the core IAM resources.
- Always verify the active identity before making IAM changes.
- IAM is the foundation of AWS security and automation.

---
