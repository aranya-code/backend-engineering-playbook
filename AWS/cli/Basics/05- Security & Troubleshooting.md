# Security, Best Practices & Troubleshooting

> Learn how to use the AWS CLI securely in production, protect AWS credentials, troubleshoot common issues, and follow AWS-recommended operational practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Secure AWS CLI credentials.
- Protect AWS accounts from credential leakage.
- Apply the Principle of Least Privilege.
- Rotate credentials safely.
- Troubleshoot authentication problems.
- Diagnose common AWS CLI failures.
- Follow production-ready security practices.

---

# Why Security Matters

AWS CLI is extremely powerful.

With a single command, you can:

- Delete S3 buckets
- Terminate EC2 instances
- Delete RDS databases
- Remove IAM users
- Delete CloudFormation stacks
- Update Route 53 records

Because AWS CLI interacts directly with AWS APIs, improper usage can lead to:

- Data loss
- Security breaches
- Unexpected costs
- Production outages

Understanding how to secure the CLI is therefore just as important as learning the commands themselves.

---

# Shared Responsibility Model

AWS follows the **Shared Responsibility Model**.

AWS is responsible for protecting the cloud infrastructure.

Customers are responsible for securing their AWS accounts and identities.

For AWS CLI users, this means protecting:

- Credentials
- IAM permissions
- Local configuration
- Automation scripts
- CI/CD pipelines

---

# Secure Authentication

Always prefer temporary credentials over long-term credentials.

Recommended order:

```
IAM Role
        ↓
IAM Identity Center (SSO)
        ↓
STS Temporary Credentials
        ↓
IAM User Access Keys
```

Avoid creating long-lived Access Keys unless absolutely necessary.

---

# Never Use the Root Account

The AWS Root User has unrestricted access to the AWS account.

Never configure the AWS CLI using Root credentials.

Use the Root User only for exceptional administrative tasks such as:

- Account recovery
- Billing management
- Organization setup
- MFA configuration

Daily operations should always use an IAM User or, preferably, an IAM Role.

---

# Apply the Principle of Least Privilege

Grant only the permissions required to perform a task.

For example, if a deployment script only uploads files to Amazon S3, it does **not** need permissions to:

- Delete IAM users
- Launch EC2 instances
- Modify Route 53 records

Instead, create a policy that grants only the required S3 permissions.

Following the Principle of Least Privilege reduces the impact of accidental or malicious actions.

---

# Protect Your Credentials

Treat AWS credentials as highly sensitive information.

Never expose:

- Access Key IDs
- Secret Access Keys
- Session Tokens

Avoid storing credentials in:

- Git repositories
- Screenshots
- Shared documents
- Email
- Chat messages
- Public code snippets

Instead, use:

- IAM Roles
- AWS IAM Identity Center
- Secure secret management solutions

---

# Rotate Access Keys

If long-term Access Keys are used, rotate them regularly.

A typical rotation process is:

1. Create a new Access Key.
2. Update applications or CLI profiles.
3. Verify the new key works.
4. Disable the old key.
5. Delete the old key after confirmation.

Avoid leaving unused keys active.

---

# Secure Your Configuration Files

AWS CLI stores configuration locally.

Typical locations:

Linux/macOS

```text
~/.aws/
```

Windows

```text
C:\Users\<username>\.aws\
```

Protect these files with appropriate file permissions.

Do not copy them between systems unless necessary.

Do not back them up to publicly accessible locations.

---

# Use Multi-Factor Authentication (MFA)

Enable MFA for:

- Root User
- Administrative IAM Users
- Privileged accounts

When using temporary credentials, MFA adds an additional layer of protection against compromised passwords or access keys.

---

# Verify Your Identity Before Making Changes

Before running commands that modify infrastructure, verify the active identity.

```bash
aws sts get-caller-identity
```

Example output:

```json
{
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:role/DeploymentRole"
}
```

This simple check helps prevent accidental changes in the wrong AWS account.

---

# Secure Automation

Automation scripts should never contain hardcoded credentials.

❌ Avoid:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

✔ Prefer:

- IAM Roles
- GitHub Actions OIDC
- AWS IAM Identity Center
- Secure CI/CD secret stores

This reduces the risk of credential exposure and simplifies credential management.

---

# Common Credential Leaks

Credential leaks commonly occur through:

- Public Git repositories
- Terminal screenshots
- Shared shell history
- Log files
- Configuration backups
- Copy-pasted examples

Always review code and documentation before sharing them publicly.

---

# Production Security Checklist

Before using AWS CLI in production, verify:

- □ AWS CLI Version 2 is installed.
- □ MFA is enabled.
- □ Root credentials are not in use.
- □ IAM Role or temporary credentials are preferred.
- □ Least Privilege policies are applied.
- □ Credentials are stored securely.
- □ Access Keys are rotated regularly.
- □ Active AWS account verified with `aws sts get-caller-identity`.
- □ Production scripts do not contain hardcoded secrets.

---

# Architecture Note

A secure authentication workflow typically looks like this:

```text
Developer
      │
      ▼
Identity Provider
      │
      ▼
AWS IAM Identity Center
      │
      ▼
Temporary Credentials
      │
      ▼
AWS CLI
      │
      ▼
AWS APIs
```

Notice that long-term credentials are eliminated from the workflow.

---

# Interview Note

### Question

What are the most important security best practices when using AWS CLI?

### Sample Answer

I avoid using the Root account, prefer IAM Roles or AWS IAM Identity Center over long-term Access Keys, follow the Principle of Least Privilege, rotate credentials regularly, verify the active identity before making production changes, and ensure credentials are never stored in source code or shared publicly.

---

# Key Takeaways

- AWS CLI has powerful administrative capabilities and must be used securely.
- Prefer temporary credentials over long-term Access Keys.
- Never use the Root account for daily work.
- Apply the Principle of Least Privilege.
- Rotate credentials regularly.
- Protect local AWS configuration files.
- Verify the active AWS identity before modifying infrastructure.

---

# Troubleshooting AWS CLI

Even experienced AWS engineers occasionally encounter errors when using the AWS CLI.

The key to effective troubleshooting is understanding **where the failure occurs**.

Most AWS CLI issues fall into one of the following categories:

- Installation
- Authentication
- Authorization
- Region configuration
- Network connectivity
- Endpoint configuration
- Service-specific errors

Rather than guessing, troubleshoot each layer methodically.

---

# A Systematic Troubleshooting Workflow

When a command fails, follow this sequence:

```text
AWS CLI Installed?
        │
        ▼
Credentials Valid?
        │
        ▼
Correct AWS Account?
        │
        ▼
Correct Region?
        │
        ▼
IAM Permissions?
        │
        ▼
Network Connectivity?
        │
        ▼
Service Availability?
```

Avoid jumping directly to IAM policies or AWS Console settings. Start with the basics.

---

# Issue 1 – AWS CLI Not Found

Example:

```text
aws: command not found
```

or on Windows:

```text
'aws' is not recognized as an internal or external command
```

### Possible Causes

- AWS CLI is not installed.
- PATH is not configured correctly.
- Terminal needs to be restarted.

### Troubleshooting

Verify installation:

```bash
aws --version
```

Locate the executable:

Linux/macOS

```bash
which aws
```

Windows

```powershell
where aws
```

If the executable cannot be located, reinstall AWS CLI Version 2.

---

# Issue 2 – Unable to Locate Credentials

Example:

```text
Unable to locate credentials
```

### Cause

AWS CLI could not find credentials in the Credential Provider Chain.

### Verify

```bash
aws configure list
```

Verify your identity:

```bash
aws sts get-caller-identity
```

### Possible Solutions

- Run:

```bash
aws configure
```

- Specify a profile:

```bash
aws s3 ls --profile development
```

- Login using AWS IAM Identity Center:

```bash
aws sso login
```

---

# Issue 3 – AccessDenied

Example:

```text
An error occurred (AccessDenied)
```

### Important

Authentication succeeded.

Authorization failed.

This means:

✔ AWS knows who you are.

❌ Your IAM identity does not have permission.

---

### Troubleshooting

Identify the current identity:

```bash
aws sts get-caller-identity
```

Review:

- IAM Policies
- Permission Boundaries
- Service Control Policies (AWS Organizations)
- Resource-based Policies

---

# Issue 4 – InvalidClientTokenId

Example:

```text
The security token included in the request is invalid.
```

Possible causes:

- Incorrect Access Key
- Incorrect Secret Key
- Disabled Access Key
- Deleted IAM User

Verify credentials:

```bash
aws configure list
```

If necessary, generate new credentials.

---

# Issue 5 – ExpiredToken

Example:

```text
ExpiredToken
```

This occurs when temporary credentials have expired.

Common scenarios:

- STS Session expired
- IAM Identity Center session expired
- Assumed Role session expired

Solution:

```bash
aws sso login
```

or assume the role again.

---

# Issue 6 – SignatureDoesNotMatch

Example:

```text
SignatureDoesNotMatch
```

Common causes:

- Incorrect Secret Access Key
- Wrong Region
- System clock drift
- Corrupted credentials

Check:

```bash
aws configure list
```

Verify:

```bash
date
```

Ensure the system clock is synchronized using NTP.

---

# Issue 7 – Incorrect Region

Symptoms include:

- Missing resources
- Resource not found
- Unexpected empty responses

Example:

```bash
aws ec2 describe-instances
```

returns:

```text
Reservations: []
```

The instances may exist in another Region.

Verify the current Region:

```bash
aws configure get region
```

Temporarily override it:

```bash
aws ec2 describe-instances \
--region us-east-1
```

---

# Issue 8 – SSL Certificate Errors

Example:

```text
SSL validation failed
```

Possible causes:

- Corporate proxy
- Self-signed certificate
- Network interception
- Incorrect CA bundle

Avoid disabling SSL verification in production.

Only use:

```bash
--no-verify-ssl
```

for temporary testing in controlled environments.

---

# Issue 9 – Endpoint Connection Error

Example:

```text
Could not connect to the endpoint URL
```

Possible causes:

- Incorrect Region
- Incorrect endpoint
- Firewall restrictions
- Internet connectivity issues
- DNS resolution problems

Verify connectivity before troubleshooting AWS resources.

---

# Using `--debug`

One of the most useful troubleshooting tools.

Example:

```bash
aws s3 ls --debug
```

Debug mode displays:

- Credential Provider Chain
- Region resolution
- Request signing
- HTTP request
- HTTP response
- Retry attempts
- Detailed error information

This is often the fastest way to identify the root cause of an issue.

---

# Troubleshooting Checklist

Before opening an AWS Support case, verify:

- □ AWS CLI Version 2 installed.
- □ Correct AWS account.
- □ Correct Region.
- □ Credentials are valid.
- □ IAM permissions are sufficient.
- □ Internet connectivity is working.
- □ DNS resolution is functioning.
- □ System clock is synchronized.
- □ No expired temporary credentials.
- □ AWS service is available in the selected Region.

---

# Production Tips

When troubleshooting:

1. Verify identity first.

```bash
aws sts get-caller-identity
```

2. Verify Region.

```bash
aws configure get region
```

3. Verify configuration.

```bash
aws configure list
```

4. Retry with:

```bash
--debug
```

This simple sequence resolves a large percentage of AWS CLI issues.

---

# Real-World Workflow

## Scenario

A deployment suddenly fails with:

```text
AccessDenied
```

Recommended workflow:

```text
Deployment Failed
        │
        ▼
Check Active Identity
        │
        ▼
Check Active Profile
        │
        ▼
Verify Region
        │
        ▼
Review IAM Policies
        │
        ▼
Retry with --debug
```

Avoid changing IAM permissions until you've confirmed the correct identity and Region.

---

# Architecture Note

Most AWS CLI errors occur **before** the request reaches the target AWS service.

```text
AWS CLI
      │
      ├── Installation
      ├── Configuration
      ├── Authentication
      ├── Authorization
      └── Network
               │
               ▼
           AWS Service
```

Understanding where the request fails significantly reduces troubleshooting time.

---

# Interview Note

### Question

How would you troubleshoot an AWS CLI command that suddenly starts returning `AccessDenied`?

### Sample Answer

I follow a structured approach:

1. Verify the active identity using `aws sts get-caller-identity`.
2. Confirm the correct profile and Region.
3. Check whether temporary credentials have expired.
4. Review IAM policies, permission boundaries, and Service Control Policies if applicable.
5. Re-run the command with `--debug` to inspect request details and identify the exact failure point.

This systematic process avoids making unnecessary configuration changes and quickly isolates the root cause.

---

# Key Takeaways

- Troubleshoot problems systematically rather than guessing.
- Separate authentication issues from authorization issues.
- Always verify the active identity and Region first.
- Use `aws configure list` and `aws sts get-caller-identity` as your primary diagnostic commands.
- Use `--debug` to inspect request processing and identify failures.
- Most AWS CLI issues can be resolved without modifying IAM policies when the root cause is identified early.

# Production Best Practices & Operational Checklists

Security is not just about protecting credentials.

It is also about building repeatable operational habits that reduce human error.

Experienced cloud engineers rely on standardized workflows before making infrastructure changes.

---

# Daily AWS CLI Checklist

Before starting work, verify your environment.

```bash
aws --version
```

Verify your identity:

```bash
aws sts get-caller-identity
```

Verify the active Region:

```bash
aws configure get region
```

Verify the active profile:

```bash
aws configure list
```

These four commands immediately confirm:

- AWS CLI version
- Current AWS account
- IAM identity
- Active Region
- Active profile

Running these commands takes only a few seconds but can prevent costly mistakes.

---

# Before Running Destructive Commands

Always pause before executing commands that delete or modify infrastructure.

Examples include:

```bash
aws s3 rm
```

```bash
aws ec2 terminate-instances
```

```bash
aws cloudformation delete-stack
```

```bash
aws rds delete-db-instance
```

Before executing these commands, confirm:

- Correct AWS account
- Correct Region
- Correct profile
- Correct resource identifier
- Appropriate permissions

Never rely solely on memory.

---

# Use Read-Only Commands First

Whenever possible, inspect resources before modifying them.

Example:

Instead of immediately stopping an instance:

```bash
aws ec2 stop-instances \
--instance-ids i-1234567890abcdef
```

First inspect it:

```bash
aws ec2 describe-instances \
--instance-ids i-1234567890abcdef
```

This confirms:

- Instance ID
- Current state
- Availability Zone
- Tags
- Instance type

---

# Use Explicit Parameters

Avoid relying on defaults.

Instead of:

```bash
aws s3 sync build/ s3://frontend
```

Prefer:

```bash
aws s3 sync build/ s3://frontend \
--profile production \
--region ap-south-1
```

Explicit commands are easier to review, troubleshoot, and reuse.

---

# Log Automation

Production automation should generate logs.

Example:

```bash
aws cloudformation deploy \
--template-file template.yaml \
>> deployment.log 2>&1
```

Logs provide:

- Audit trails
- Easier troubleshooting
- Deployment history
- Operational visibility

---

# Validate Before Deploying

Whenever AWS provides a validation command, use it.

Example:

CloudFormation:

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

Validation catches errors before changes reach production.

---

# Prefer Idempotent Operations

Automation should be safe to execute multiple times.

Good examples:

```bash
aws s3 sync
```

```bash
aws cloudformation deploy
```

These commands compare the desired state with the current state and apply only the necessary changes.

Whenever possible, design scripts so repeated execution does not produce unintended side effects.

---

# Keep Scripts Modular

Instead of writing one large script:

```
deploy.sh
```

Split functionality into smaller scripts.

Example:

```
login.sh

validate.sh

deploy.sh

verify.sh

rollback.sh
```

Advantages:

- Easier testing
- Simpler maintenance
- Better reuse
- Clearer responsibilities

---

# Secure CI/CD Pipelines

Production deployment pipelines should:

- Use temporary credentials.
- Authenticate with IAM Roles or OIDC.
- Avoid hardcoded secrets.
- Limit permissions.
- Log deployment activities.
- Validate infrastructure before deployment.

Never expose credentials in pipeline logs.

---

# Incident Response Checklist

When an unexpected issue occurs:

1. Verify the active identity.

```bash
aws sts get-caller-identity
```

2. Verify the active Region.

```bash
aws configure get region
```

3. Verify the active profile.

```bash
aws configure list
```

4. Enable debug logging.

```bash
aws s3 ls --debug
```

5. Review recent infrastructure changes.

Avoid making additional changes until the root cause has been identified.

---

# Common Anti-Patterns

## Using the Default Profile Everywhere

Avoid managing every environment through the default profile.

Prefer:

```
development

testing

staging

production
```

Separate profiles reduce the risk of accidental deployments.

---

## Hardcoding Resource IDs

Avoid:

```bash
INSTANCE=i-0123456789abcdef
```

for every script.

Prefer discovering resources dynamically when appropriate.

Example:

```bash
aws ec2 describe-instances \
--filters "Name=tag:Environment,Values=Production"
```

---

## Running Commands Without Verification

Never assume you are connected to the correct AWS account.

Always verify using:

```bash
aws sts get-caller-identity
```

---

## Ignoring Exit Codes

Incorrect:

```bash
aws s3 sync build/ s3://frontend

echo "Deployment complete"
```

Correct:

```bash
aws s3 sync build/ s3://frontend

if [ $? -ne 0 ]
then
    echo "Deployment failed."
    exit 1
fi
```

---

# Senior Engineer Recommendations

Experienced engineers typically follow these habits:

- Prefer IAM Roles over IAM Users.
- Verify identity before making production changes.
- Use Named Profiles instead of repeatedly running `aws configure`.
- Store infrastructure definitions in version control.
- Automate repetitive tasks.
- Keep commands explicit and readable.
- Review destructive commands carefully before execution.
- Write automation that is repeatable and idempotent.

---

# Real-World Workflow

## Scenario

You need to deploy a CloudFormation stack to production.

A recommended workflow is:

```text
Verify AWS Identity
        │
        ▼
Verify Region
        │
        ▼
Validate Template
        │
        ▼
Review Parameters
        │
        ▼
Deploy Stack
        │
        ▼
Monitor Events
        │
        ▼
Verify Resources
```

This process minimizes deployment risks and improves operational confidence.

---

# Architecture Note

Successful AWS operations rely on multiple layers working together.

```text
Engineer
      │
      ▼
Shell Script
      │
      ▼
AWS CLI
      │
      ▼
IAM Authentication
      │
      ▼
AWS APIs
      │
      ▼
Cloud Resources
      │
      ▼
CloudWatch Logs & Monitoring
```

Each layer should be observable, secure, and repeatable.

---

# Interview Note

### Question

What operational practices do you follow when using the AWS CLI in production?

### Sample Answer

Before making changes, I verify the active AWS account, Region, and IAM identity. I prefer temporary credentials, avoid the Root account, use explicit Regions and profiles in scripts, validate infrastructure definitions before deployment, capture logs for auditing, and design automation to be idempotent and resilient. For troubleshooting, I use `aws sts get-caller-identity`, `aws configure list`, and `--debug` to isolate issues systematically.

---

# Chapter Summary

In this chapter, you learned:

- AWS CLI security principles
- Protecting credentials
- Least Privilege access
- Credential rotation
- Secure automation
- Common authentication and authorization errors
- Systematic troubleshooting
- Production operational practices
- CI/CD security recommendations
- Senior engineering workflows

Following these practices will help you build secure, reliable, and maintainable AWS CLI workflows suitable for production environments.

---
