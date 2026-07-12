# IAM Identity Center (SSO)

> Learn how to manage AWS IAM Identity Center (formerly AWS Single Sign-On) using the AWS CLI. This chapter covers Single Sign-On (SSO), Permission Sets, Identity Sources, AWS Organizations integration, CLI authentication, and enterprise access management.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand AWS IAM Identity Center
- Configure AWS CLI with SSO
- Manage Permission Sets
- Understand Identity Sources
- Integrate with AWS Organizations
- Authenticate using SSO
- Manage enterprise access
- Apply production SSO best practices

---

# What is IAM Identity Center?

AWS IAM Identity Center is AWS's centralized identity and access management solution.

It enables users to:

- Sign in once
- Access multiple AWS accounts
- Access cloud applications
- Eliminate long-lived IAM Users
- Manage permissions centrally

IAM Identity Center was formerly known as **AWS Single Sign-On (AWS SSO)**.

---

# Why Use IAM Identity Center?

Instead of creating IAM Users in every AWS account:

```text
Developer

↓

AWS Account A

↓

IAM User
```

Use:

```text
Developer

↓

IAM Identity Center

↓

Multiple AWS Accounts
```

Benefits include:

- Centralized authentication
- Simplified permission management
- Reduced administrative overhead
- Improved security

---

# Identity Center Architecture

```text
User
   │
   ▼
Identity Center
   │
   ▼
Permission Set
   │
   ▼
AWS Account
   │
   ▼
IAM Role
   │
   ▼
AWS Resources
```

Identity Center automatically creates IAM Roles in target AWS accounts based on assigned Permission Sets.

---

# Identity Sources

IAM Identity Center supports multiple identity providers.

Supported identity sources include:

- Identity Center Directory
- Active Directory
- External Identity Providers
- Microsoft Entra ID (Azure AD)
- Okta
- Ping Identity

This enables centralized user management.

---

# Authentication Flow

```text
User
    │
    ▼
Login
    │
    ▼
Identity Provider
    │
    ▼
Identity Center
    │
    ▼
Permission Set
    │
    ▼
Temporary Credentials
    │
    ▼
AWS Resources
```

Users receive temporary credentials instead of long-lived Access Keys.

---

# AWS CLI Authentication with SSO

Configure AWS CLI for SSO:

```bash
aws configure sso
```

The CLI prompts for:

- SSO Session Name
- Start URL
- AWS Region
- AWS Account
- Permission Set

After configuration, a profile is created.

---

# Example Configuration

```text
SSO session name:

company

SSO start URL:

https://company.awsapps.com/start

SSO Region:

ap-south-1

AWS Account:

Production

Permission Set:

AdministratorAccess
```

---

# Login Using SSO

Authenticate:

```bash
aws sso login
```

A browser opens for authentication.

After successful login:

```text
Temporary Credentials

↓

Stored Securely

↓

CLI Ready
```

---

# List Available Profiles

```bash
aws configure list-profiles
```

Example:

```text
default

development

production

sandbox
```

---

# Use an SSO Profile

```bash
aws s3 ls \
--profile production
```

or

```bash
aws ec2 describe-instances \
--profile production
```

---

# Verify Current Identity

```bash
aws sts get-caller-identity \
--profile production
```

Always verify the active account before making changes.

---

# Logout

Remove cached SSO credentials.

```bash
aws sso logout
```

Useful when switching users or devices.

---

# Permission Sets

Permission Sets define what users can do after authentication.

They are similar to IAM Policies but are managed centrally.

Example:

```text
ReadOnly

Developer

Administrator

Billing
```

Each Permission Set maps to an IAM Role in the target account.

---

# Permission Set Workflow

```text
Permission Set
      │
      ▼
Assigned User
      │
      ▼
AWS Account
      │
      ▼
IAM Role
      │
      ▼
Temporary Credentials
```

---

# Multiple AWS Accounts

One user can access multiple AWS accounts.

Example:

```text
Identity Center

├── Development

├── Testing

├── Production

└── Shared Services
```

Each account can have different Permission Sets.

---

# AWS Organizations Integration

IAM Identity Center integrates with AWS Organizations.

```text
AWS Organizations
        │
        ▼
Identity Center
        │
        ▼
Permission Sets
        │
        ▼
Member Accounts
```

This enables centralized administration across hundreds of AWS accounts.

---

# Credential Storage

After authentication:

```text
Browser Login

↓

STS Credentials

↓

Local Cache

↓

AWS CLI
```

Credentials automatically expire.

---

# Session Expiration

SSO sessions have a configurable duration.

When expired:

```bash
aws sso login
```

must be executed again.

---

# Common Errors

## UnauthorizedException

Cause:

The SSO session has expired.

Solution:

```bash
aws sso login
```

---

## Profile Not Found

Example:

```text
The config profile could not be found.
```

Verify:

```bash
aws configure list-profiles
```

---

## AccessDenied

Possible causes:

- Missing Permission Set
- Incorrect AWS Account
- SCP restrictions
- IAM Role permissions

---

# Production Best Practices

## Prefer SSO

For human users:

```text
IAM Identity Center

✓ Recommended
```

Instead of:

```text
IAM Users

✗ Avoid where possible
```

---

## Use IAM Roles

Identity Center automatically provisions IAM Roles.

Avoid distributing Access Keys to employees.

---

## Verify Active Account

Before running commands:

```bash
aws sts get-caller-identity
```

Many production mistakes occur because engineers are logged into the wrong account.

---

## Separate Permission Sets

Example:

```text
Developers

↓

DeveloperAccess

Operations

↓

OperationsAccess

Security

↓

SecurityAudit

Administrators

↓

AdministratorAccess
```

Avoid sharing administrative Permission Sets broadly.

---

## Follow Least Privilege

Create Permission Sets with only the permissions required.

Avoid assigning full administrative access unless necessary.

---

# Real-World Workflow

A new engineer joins the company.

```text
Create User
      │
      ▼
Assign Identity Source
      │
      ▼
Assign Permission Set
      │
      ▼
Assign AWS Accounts
      │
      ▼
Configure AWS CLI
      │
      ▼
aws sso login
      │
      ▼
Access AWS Resources
```

---

# Architecture Note

```text
Developer
      │
      ▼
IAM Identity Center
      │
      ▼
Permission Set
      │
      ▼
IAM Role
      │
      ▼
STS Temporary Credentials
      │
      ▼
AWS Services
```

Identity Center removes the need for long-lived IAM Users and Access Keys for human users.

---

# Interview Note

### Question

**What is the difference between IAM Users and IAM Identity Center?**

### Answer

IAM Users are identities created within a single AWS account and typically use long-lived credentials such as passwords and Access Keys. IAM Identity Center provides centralized authentication and authorization across multiple AWS accounts, integrates with enterprise identity providers, and issues temporary credentials through IAM Roles. For organizations managing multiple AWS accounts, IAM Identity Center is the recommended solution because it simplifies access management, improves security, and reduces reliance on long-lived credentials.

---

# Key Takeaways

- IAM Identity Center provides centralized authentication across AWS accounts.
- AWS CLI supports SSO using `aws configure sso` and `aws sso login`.
- Permission Sets define access and are translated into IAM Roles.
- Temporary credentials improve security by eliminating long-lived Access Keys.
- Identity Center integrates with AWS Organizations and enterprise identity providers.
- Always verify the active AWS account before making changes.
- Follow the Principle of Least Privilege when assigning Permission Sets.

---
