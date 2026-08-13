# Troubleshooting & Best Practices

> Learn how to troubleshoot common AWS IAM issues using the AWS CLI and follow production-ready security practices for identity and access management. This chapter covers permission debugging, policy evaluation, authentication problems, and operational best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot common IAM CLI errors
- Investigate AccessDenied errors
- Debug IAM policies
- Troubleshoot IAM Roles and STS
- Diagnose SSO authentication issues
- Audit IAM security
- Apply production-ready IAM best practices

---

# Why Troubleshooting IAM Matters

Most AWS permission problems are caused by configuration—not by AWS service failures.

Common causes include:

- Incorrect IAM Policies
- Explicit Deny
- Wrong IAM Role
- Missing Trust Policy
- Permission Boundary
- SCP (Service Control Policy)
- Resource Policy
- Expired Credentials
- Wrong AWS Account

A structured troubleshooting process prevents unnecessary changes and reduces downtime.

---

# IAM Troubleshooting Workflow

Whenever an IAM-related issue occurs:

```text
Verify AWS Account
        │
        ▼
Verify Identity
        │
        ▼
Authentication Successful?
        │
        ▼
Check IAM Policies
        │
        ▼
Check Explicit Deny
        │
        ▼
Check Resource Policy
        │
        ▼
Check SCP
        │
        ▼
Check Permission Boundary
        │
        ▼
Retry
```

Always follow this order.

---

# Verify Your Identity

Always begin with:

```bash
aws sts get-caller-identity
```

Example output:

```json
{
    "Account":"123456789012",
    "Arn":"arn:aws:iam::123456789012:user/backend-admin"
}
```

This confirms:

- Current AWS account
- Current identity
- ARN

---

# Verify AWS CLI Configuration

```bash
aws configure list
```

Check:

- Access Key
- Secret Key
- Region
- Profile

---

# Verify Active Profile

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

Use the correct profile:

```bash
aws sts get-caller-identity \
--profile production
```

---

# Error: AccessDenied

Example:

```text
AccessDenied
```

Possible causes:

- Missing IAM permission
- Explicit Deny
- SCP restriction
- Permission Boundary
- Resource Policy

This is the most common IAM error.

---

# Error: AccessDenied During S3 Operations

Example:

```bash
aws s3 ls
```

Returns:

```text
AccessDenied
```

Verify:

- IAM Policy
- Bucket Policy
- SCP
- Permission Boundary

Remember:

S3 authorization also evaluates bucket policies.

---

# Error: UnauthorizedOperation

Example:

```text
UnauthorizedOperation
```

Usually occurs with:

- EC2
- EBS
- Networking

Cause:

The IAM identity lacks the required permission.

---

# Error: InvalidClientTokenId

Example:

```text
InvalidClientTokenId
```

Possible causes:

- Incorrect Access Key
- Deleted Access Key
- Wrong profile
- Wrong credentials

Verify:

```bash
aws configure list
```

---

# Error: SignatureDoesNotMatch

Example:

```text
SignatureDoesNotMatch
```

Possible causes:

- Wrong Secret Key
- Wrong Region
- Incorrect system time

Verify:

```bash
aws configure get region
```

---

# Error: ExpiredToken

Example:

```text
ExpiredToken
```

Cause:

Temporary credentials expired.

Solutions:

For SSO:

```bash
aws sso login
```

For AssumeRole:

Assume the role again.

---

# Error: NoSuchEntity

Example:

```text
NoSuchEntity
```

Verify:

- User Name
- Group Name
- Role Name
- Policy ARN

IAM names are case-sensitive.

---

# Error: EntityAlreadyExists

Example:

```text
EntityAlreadyExists
```

The resource already exists.

Verify:

```bash
aws iam list-users
```

or

```bash
aws iam list-roles
```

---

# Error: DeleteConflict

Example:

```text
DeleteConflict
```

Cause:

Dependencies still exist.

Examples:

- Attached Policies
- Access Keys
- Group Membership
- Instance Profiles

Remove dependencies first.

---

# Troubleshooting AssumeRole

Unable to assume a role?

Verify:

- Trust Policy
- IAM Permission
- Role ARN
- Account ID

Example:

```bash
aws sts assume-role \
--role-arn arn:aws:iam::123456789012:role/AdminRole \
--role-session-name AdminSession
```

---

# Troubleshooting Trust Policies

Verify:

```bash
aws iam get-role \
--role-name BackendEC2Role
```

Review:

```text
AssumeRolePolicyDocument
```

Incorrect principals are a common cause of AssumeRole failures.

---

# Troubleshooting Permission Evaluation

AWS evaluates permissions in this order:

```text
Authentication
      │
      ▼
Explicit Deny
      │
      ▼
SCP
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
Allow / Deny
```

Understanding this flow is essential when diagnosing complex permission issues.

---

# Debugging with --debug

Enable verbose logging:

```bash
aws iam list-users \
--debug
```

Useful information includes:

- Credential provider chain
- HTTP request
- Request signing
- Retry attempts
- HTTP response

---

# Credential Report Audit

Generate:

```bash
aws iam generate-credential-report
```

Retrieve:

```bash
aws iam get-credential-report
```

Review:

- Old Access Keys
- Users without MFA
- Inactive users
- Password age

---

# Access Analyzer Review

List analyzers:

```bash
aws accessanalyzer list-analyzers
```

List findings:

```bash
aws accessanalyzer list-findings \
--analyzer-name OrganizationAnalyzer
```

Review findings regularly.

---

# Production Security Checklist

Before granting permissions:

- □ Verify AWS account.
- □ Verify IAM identity.
- □ Follow Least Privilege.
- □ Avoid wildcard permissions.
- □ Enable MFA.
- □ Prefer IAM Roles.
- □ Review Permission Boundaries.
- □ Review SCPs.
- □ Audit Access Analyzer findings.

---

# Production Best Practices

## Prefer IAM Roles

Instead of:

```text
IAM User

↓

Access Keys
```

Use:

```text
IAM Role

↓

Temporary Credentials
```

---

## Avoid AdministratorAccess

Instead of:

```text
AdministratorAccess
```

Create narrowly scoped Customer Managed Policies.

---

## Rotate Credentials

Regularly rotate:

- Access Keys
- Secrets
- Certificates

Remove unused credentials.

---

## Enable MFA

Enable MFA for:

- Root User
- Administrators
- Privileged users

---

## Review Policies Regularly

Audit:

- Wildcard permissions
- Unused policies
- Old roles
- Dormant users

---

## Use Customer Managed Policies

Avoid excessive use of AWS Managed Policies in production.

Customer Managed Policies provide:

- Better control
- Versioning
- Easier auditing

---

# Real-World Troubleshooting Workflow

Developer receives AccessDenied.

```text
Verify Identity
      │
      ▼
Verify Account
      │
      ▼
Review IAM Policy
      │
      ▼
Review Resource Policy
      │
      ▼
Review SCP
      │
      ▼
Review Permission Boundary
      │
      ▼
Retry
```

Avoid changing policies until the root cause is identified.

---

# Architecture Note

```text
AWS CLI
      │
      ▼
Authentication
      │
      ▼
IAM Evaluation
      │
      ├── SCP
      ├── Permission Boundary
      ├── Identity Policy
      ├── Resource Policy
      └── Explicit Deny
      │
      ▼
AWS Service
```

Every AWS request passes through this authorization pipeline.

---

# Interview Note

### Question

**How would you troubleshoot an `AccessDenied` error in AWS?**

### Answer

I begin by verifying the active identity using `aws sts get-caller-identity` and confirm that I am working in the correct AWS account and Region. Next, I review the IAM identity policies to ensure the required action is allowed. If the permission still fails, I check for explicit deny statements, resource-based policies, Service Control Policies (SCPs), and Permission Boundaries. If temporary credentials are being used, I verify they have not expired. Finally, I rerun the command with `--debug` if additional diagnostic information is required.

---

# Key Takeaways

- Most IAM issues are caused by policy configuration rather than AWS failures.
- Always verify the active AWS identity before troubleshooting.
- Understand the IAM policy evaluation logic.
- Review SCPs, Permission Boundaries, and Resource Policies in addition to IAM Policies.
- Use Credential Reports and Access Analyzer to improve security posture.
- Prefer IAM Roles and temporary credentials over long-lived Access Keys.
- Follow the Principle of Least Privilege in every production environment.

---
