# 02 - Configuring AWS Credentials

## Overview

Before Boto3 can interact with Amazon DynamoDB or any other AWS service, it must authenticate with AWS.

Authentication is handled through **AWS credentials**, which consist of:

- Access Key ID
- Secret Access Key
- (Optional) Session Token

However, **production applications should rarely use long-lived access keys**. Instead, AWS recommends using **IAM Roles** whenever possible.

Understanding the AWS Credential Provider Chain is essential for building secure applications.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How Boto3 authenticates
- The AWS Credential Provider Chain
- Environment variables
- AWS CLI credentials
- Named profiles
- IAM Roles
- EC2 Instance Profiles
- Lambda Execution Roles
- Temporary credentials
- Production security best practices

---

# Why Authentication Matters

Every request sent to AWS must be authenticated.

```text
Python Application

↓

Boto3

↓

AWS Credentials

↓

Request Signing

↓

DynamoDB
```

Without valid credentials:

```text
AccessDeniedException
```

will be returned.

---

# AWS Credentials

AWS credentials usually consist of:

```text
Access Key ID

Secret Access Key

(Optional)

Session Token
```

Example

```text
Access Key ID

AKIA****************

Secret Access Key

************************
```

Never expose these values publicly.

---

# AWS Credential Provider Chain

Boto3 searches for credentials automatically.

The search order is called the **Credential Provider Chain**.

```text
Explicit Credentials

↓

Environment Variables

↓

AWS Credentials File

↓

AWS Config File

↓

Named Profile

↓

IAM Role

↓

Container Credentials

↓

EC2 Instance Profile
```

The first valid credentials found are used.

---

# Provider 1 — Explicit Credentials

Credentials can be passed directly.

```python
import boto3

client = boto3.client(
    "dynamodb",
    aws_access_key_id="ACCESS_KEY",
    aws_secret_access_key="SECRET_KEY",
)
```

Although supported, this approach should generally be avoided outside of testing.

---

# Provider 2 — Environment Variables

Boto3 automatically checks environment variables.

```bash
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
export AWS_DEFAULT_REGION=us-east-1
```

Windows PowerShell:

```powershell
$env:AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
$env:AWS_DEFAULT_REGION="us-east-1"
```

Advantages:

- Simple
- Works well locally
- Common in CI/CD

---

# Provider 3 — AWS Credentials File

Location:

Linux/macOS

```text
~/.aws/credentials
```

Windows

```text
C:\Users\<username>\.aws\credentials
```

Example

```ini
[default]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
```

---

# Provider 4 — AWS Config File

Location:

```text
~/.aws/config
```

Example

```ini
[default]
region=us-east-1
output=json
```

This file stores configuration rather than secrets.

---

# Named Profiles

Multiple AWS accounts can be managed using profiles.

Credentials file:

```ini
[default]
aws_access_key_id=...

[development]
aws_access_key_id=...

[production]
aws_access_key_id=...
```

Using a profile:

```python
session = boto3.Session(profile_name="development")
```

This is useful when working across multiple AWS accounts.

---

# Sessions

Create a session with a profile.

```python
import boto3

session = boto3.Session(profile_name="production")

dynamodb = session.resource("dynamodb")
```

Sessions allow different credential sets to coexist within the same application.

---

# IAM Roles

The preferred authentication method on AWS.

```text
EC2

↓

IAM Role

↓

Temporary Credentials

↓

Boto3
```

No credentials are stored in the application.

---

# Lambda Execution Role

AWS Lambda automatically receives temporary credentials.

```text
Lambda

↓

Execution Role

↓

Boto3

↓

DynamoDB
```

Example:

```python
import boto3

table = boto3.resource("dynamodb").Table("Orders")
```

No keys are required.

---

# EC2 Instance Profile

Applications running on EC2 should also use IAM Roles.

```text
EC2

↓

Instance Profile

↓

Temporary Credentials

↓

AWS Metadata Service

↓

Boto3
```

The SDK retrieves credentials automatically.

---

# ECS Task Roles

Containers running in Amazon ECS can receive credentials without storing secrets.

```text
ECS Task

↓

Task Role

↓

Temporary Credentials

↓

Boto3
```

---

# EKS IAM Roles for Service Accounts (IRSA)

Kubernetes workloads on Amazon EKS can use IAM Roles.

```text
Pod

↓

Service Account

↓

IAM Role

↓

Boto3
```

No static credentials are needed inside containers.

---

# Temporary Credentials

Temporary credentials include:

- Access Key
- Secret Key
- Session Token

```text
STS

↓

Temporary Credentials

↓

Expire Automatically
```

Advantages:

- Reduced security risk
- Automatic rotation
- No long-lived secrets

---

# AWS STS

Applications can assume another IAM Role.

```python
sts = boto3.client("sts")
```

Example workflow:

```text
Application

↓

AssumeRole()

↓

Temporary Credentials

↓

Access DynamoDB
```

Useful for cross-account access.

---

# Cross-Account Access

Large organizations often have multiple AWS accounts.

```text
Development Account

↓

Assume Role

↓

Production Account

↓

DynamoDB
```

This avoids sharing permanent credentials.

---

# Credential Resolution Example

Application starts.

```text
Boto3

↓

Environment Variables?

↓

NO

↓

Credentials File?

↓

YES

↓

Authenticate
```

The search stops after finding the first valid credentials.

---

# Common Authentication Errors

Typical issues include:

```text
NoCredentialsError
```

Meaning:

No credentials found.

---

```text
AccessDeniedException
```

Meaning:

Credentials exist but lack permissions.

---

```text
ExpiredTokenException
```

Meaning:

Temporary credentials have expired.

---

# Debugging Credentials

Determine which identity is being used.

```python
import boto3

sts = boto3.client("sts")

print(sts.get_caller_identity())
```

Useful when troubleshooting IAM issues.

---

# Production Architecture

```text
            FastAPI

               │

               ▼

            Boto3

               │

        Credential Chain

               │

               ▼

           IAM Role

               │

               ▼

          Amazon DynamoDB
```

---

# Performance Considerations

Authentication itself is lightweight, but repeatedly creating sessions is unnecessary.

Recommended:

```python
session = boto3.Session()
```

Reuse the session throughout the application.

---

# Security Best Practices

- Prefer IAM Roles over access keys.
- Never commit credentials to Git.
- Rotate long-lived credentials.
- Use AWS Secrets Manager for application secrets.
- Apply least-privilege IAM policies.
- Enable MFA for privileged users.
- Enable CloudTrail auditing.
- Avoid sharing credentials between environments.

---

# Best Practices

- Use named profiles for local development.
- Use IAM Roles in AWS environments.
- Keep credentials outside application code.
- Reuse Boto3 sessions.
- Validate permissions using least privilege.
- Monitor IAM activity regularly.

---

# Common Mistakes

## Hardcoding Credentials

Poor:

```python
client = boto3.client(
    "dynamodb",
    aws_access_key_id="ABC...",
    aws_secret_access_key="XYZ..."
)
```

Instead, rely on the credential provider chain.

---

## Using Root Account Credentials

Never develop applications using the AWS root account.

Create IAM users or roles instead.

---

## Committing Credentials to Git

Never store:

```text
.env

credentials

AWS keys
```

inside public repositories.

---

## Giving AdministratorAccess

Applications rarely require full AWS permissions.

Grant only the permissions they actually need.

---

# Interview Notes

A common interview question is:

> **How does Boto3 find AWS credentials?**

Boto3 uses the AWS Credential Provider Chain, checking sources such as explicit credentials, environment variables, shared credentials files, named profiles, IAM roles, and instance or task metadata until valid credentials are found.

---

Another common question is:

> **Why are IAM Roles preferred over Access Keys?**

IAM Roles provide temporary credentials that rotate automatically and eliminate the need to store long-lived secrets in applications, making them significantly more secure.

---

Another common question is:

> **How does a Lambda function authenticate with DynamoDB?**

Lambda automatically receives temporary credentials through its execution role. Boto3 retrieves these credentials without requiring access keys in the application code.

---

Another common question is:

> **What is AWS STS used for?**

AWS Security Token Service (STS) issues temporary credentials, commonly used for assuming IAM roles, cross-account access, and short-lived authenticated sessions.

---

# Key Takeaways

- Boto3 authenticates using the AWS Credential Provider Chain.
- IAM Roles are the recommended authentication mechanism for applications running on AWS.
- Named profiles simplify local development across multiple AWS accounts.
- Temporary credentials issued by STS improve security through automatic expiration.
- Never hardcode credentials or commit them to source control; always follow least-privilege IAM practices.