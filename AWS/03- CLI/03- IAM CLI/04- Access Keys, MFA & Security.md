# Access Keys, MFA & Security

> Learn how to securely manage IAM credentials using the AWS CLI. This chapter covers Access Keys, Multi-Factor Authentication (MFA), password policies, credential reports, IAM Access Analyzer, and production security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create and manage Access Keys
- Rotate Access Keys securely
- Configure Multi-Factor Authentication (MFA)
- Manage IAM Password Policies
- Generate Credential Reports
- Use IAM Access Analyzer
- Audit IAM security
- Apply AWS security best practices

---

# Why IAM Security Matters

IAM is the first line of defense for your AWS account.

Poor IAM security can result in:

- Account compromise
- Data breaches
- Privilege escalation
- Unauthorized infrastructure changes
- Financial loss

AWS recommends minimizing long-lived credentials and using temporary credentials wherever possible.

---

# Authentication Methods

AWS supports multiple authentication methods.

```text
IAM User
    │
    ├── Console Password
    ├── Access Keys
    ├── MFA
    └── Temporary Credentials (STS)
```

Production workloads should primarily use **IAM Roles** and **temporary credentials**.

---

# Access Keys

An Access Key consists of:

- Access Key ID
- Secret Access Key

Example:

```text
Access Key ID

AKIAXXXXXXXXXXXXXXXX

Secret Access Key

********************************
```

The secret key is displayed only once when created.

---

# List Access Keys

```bash
aws iam list-access-keys \
--user-name backend-admin
```

Example output:

```json
{
    "AccessKeyMetadata": [
        {
            "AccessKeyId": "AKIA****************",
            "Status": "Active"
        }
    ]
}
```

---

# Create an Access Key

```bash
aws iam create-access-key \
--user-name backend-admin
```

AWS returns:

- Access Key ID
- Secret Access Key

Store the secret securely because it cannot be retrieved again.

---

# Update an Access Key

Disable an access key.

```bash
aws iam update-access-key \
--user-name backend-admin \
--access-key-id AKIAXXXXXXXXXXXXXXXX \
--status Inactive
```

Possible statuses:

- Active
- Inactive

---

# Delete an Access Key

```bash
aws iam delete-access-key \
--user-name backend-admin \
--access-key-id AKIAXXXXXXXXXXXXXXXX
```

Delete unused keys immediately.

---

# Access Key Rotation

Recommended workflow:

```text
Create New Key
      │
      ▼
Update Applications
      │
      ▼
Test Connectivity
      │
      ▼
Disable Old Key
      │
      ▼
Delete Old Key
```

AWS recommends rotating Access Keys regularly.

---

# Temporary Credentials

Instead of Access Keys:

```text
IAM Role

↓

STS

↓

Temporary Credentials
```

Advantages:

- Automatically expire
- Lower security risk
- No manual rotation
- Preferred for AWS workloads

---

# Multi-Factor Authentication (MFA)

MFA adds a second authentication factor.

```text
Password

+

MFA Code

↓

Authentication
```

Supported devices:

- Virtual Authenticator Apps
- Hardware Tokens
- FIDO Security Keys

---

# Why MFA is Important

Without MFA:

```text
Password Stolen

↓

Account Compromised
```

With MFA:

```text
Password Stolen

↓

MFA Required

↓

Access Denied
```

MFA significantly improves account security.

---

# List MFA Devices

```bash
aws iam list-mfa-devices \
--user-name backend-admin
```

---

# Enable MFA

MFA devices are typically activated using the AWS Management Console.

After activation, they can be managed using the AWS CLI.

---

# Password Policy

Password Policies apply to IAM Users accessing the AWS Console.

Typical requirements include:

- Minimum length
- Uppercase letters
- Lowercase letters
- Numbers
- Symbols
- Password expiration

---

# View Password Policy

```bash
aws iam get-account-password-policy
```

---

# Create or Update Password Policy

```bash
aws iam update-account-password-policy \
--minimum-password-length 14 \
--require-uppercase-characters \
--require-lowercase-characters \
--require-numbers \
--require-symbols
```

This updates the account-wide password policy.

---

# Credential Reports

Credential Reports provide an overview of IAM security.

The report includes:

- Users
- Password status
- MFA status
- Access Key age
- Password age
- Last login
- Access Key usage

---

# Generate Credential Report

```bash
aws iam generate-credential-report
```

Generation is asynchronous.

---

# Download Credential Report

```bash
aws iam get-credential-report
```

The report is returned as a Base64-encoded CSV.

---

# IAM Access Analyzer

IAM Access Analyzer identifies resources that are shared outside your AWS account.

It helps detect:

- Public S3 buckets
- Cross-account access
- External principals
- Resource sharing

---

# List Access Analyzers

```bash
aws accessanalyzer list-analyzers
```

---

# List Findings

```bash
aws accessanalyzer list-findings \
--analyzer-name OrganizationAnalyzer
```

Review findings regularly.

---

# Security Audit Workflow

```text
Credential Report
        │
        ▼
Review Users
        │
        ▼
Review Access Keys
        │
        ▼
Review MFA
        │
        ▼
Review Policies
        │
        ▼
Review Access Analyzer
```

Regular audits help maintain a secure AWS environment.

---

# Common Errors

## AccessDenied

Possible causes:

- Missing IAM permissions
- SCP restrictions
- Permission Boundary
- Explicit Deny

---

## NoSuchEntity

Verify:

- User Name
- Access Key ID
- MFA Device ARN

---

## DeleteConflict

The resource still has dependencies.

Examples:

- Active Access Keys
- MFA Device
- Login Profile

Remove dependencies before deletion.

---

# Production Best Practices

## Avoid Root User

Use the root account only for:

- Initial account setup
- Billing
- Root-only operations

Never use the root account for daily administration.

---

## Enable MFA Everywhere

Enable MFA for:

- Root User
- Administrators
- Privileged IAM Users

---

## Rotate Access Keys

Recommended:

- Every 90 days (or according to your organization's security policy)
- Remove unused keys immediately.

---

## Prefer IAM Roles

Instead of:

```text
Access Keys
```

Use:

```text
IAM Roles
```

Roles eliminate long-lived credentials.

---

## Review Credential Reports

Generate reports regularly to identify:

- Inactive users
- Old access keys
- Users without MFA
- Stale passwords

---

## Enable Access Analyzer

Review findings regularly.

Remove unnecessary external access.

---

## Follow Least Privilege

Grant only the permissions required.

Avoid:

```text
AdministratorAccess
```

unless absolutely necessary.

---

# Real-World Workflow

Provisioning a secure developer account.

```text
Create User
      │
      ▼
Assign Group
      │
      ▼
Enable MFA
      │
      ▼
Create Access Key (if required)
      │
      ▼
Rotate Keys Regularly
      │
      ▼
Review Credential Reports
```

---

# Architecture Note

```text
IAM User
      │
      ▼
Authentication
      │
      ├── Password
      ├── MFA
      ├── Access Key
      └── STS Credentials
      │
      ▼
IAM Policies
      │
      ▼
AWS Resources
```

Strong authentication combined with least-privilege authorization forms the foundation of AWS security.

---

# Interview Note

### Question

**Why are IAM Roles preferred over Access Keys?**

### Answer

IAM Roles provide temporary credentials through AWS Security Token Service (STS), eliminating the need for long-lived Access Keys. Temporary credentials automatically expire, reduce the risk of credential leakage, simplify rotation, and integrate seamlessly with AWS services such as EC2, Lambda, ECS, and EKS. For these reasons, AWS recommends using IAM Roles whenever possible.

---

# Key Takeaways

- Access Keys provide programmatic access but should be minimized.
- Rotate Access Keys regularly and delete unused credentials.
- Enable MFA for all privileged users.
- Configure strong account password policies.
- Generate Credential Reports to audit IAM security.
- Use IAM Access Analyzer to detect unintended external access.
- Prefer IAM Roles and temporary credentials over long-lived Access Keys.
- Apply the Principle of Least Privilege to every IAM identity.

---
