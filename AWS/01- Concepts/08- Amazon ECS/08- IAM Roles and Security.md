# ECS IAM Roles and Security

# Why Security Matters

Containers are not security boundaries.

A compromised container can potentially access:

- AWS APIs
- Databases
- Storage
- Internal Services

Security in ECS is primarily enforced through:

```text
IAM
Networking
Encryption
Secrets Management
```

---

# ECS Security Architecture

```text
Application
     ↓
Task Role
     ↓
AWS Services

ECS Agent
     ↓
Execution Role
     ↓
ECR / CloudWatch
```

Understanding role separation is critical.

---

# IAM Fundamentals

IAM (Identity and Access Management) controls:

- Who can access AWS
- What they can access
- Which actions they can perform

Example:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "*"
}
```

---

# Principle of Least Privilege

Golden Rule:

```text
Grant Only Required Permissions
```

Avoid:

```text
AdministratorAccess
```

For ECS workloads.

---

# ECS IAM Roles

Three IAM roles are commonly used:

```text
Task Role
Task Execution Role
EC2 Instance Profile
```

Each serves a different purpose.

---

# Task Role

## What is a Task Role?

A Task Role is assumed by the application container.

Used when application code needs AWS access.

Example:

```python
import boto3

s3 = boto3.client("s3")
```

The container needs permissions.

---

# Example Use Cases

Application accessing:

- S3
- DynamoDB
- SQS
- SNS
- Secrets Manager

---

# Example Policy

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject"
  ],
  "Resource": "*"
}
```

---

# Task Role Flow

```text
Container
    ↓
Task Role
    ↓
AWS Service
```

Application receives temporary credentials.

---

# Why Task Roles Are Important

Avoids:

```text
AWS_ACCESS_KEY
AWS_SECRET_KEY
```

inside containers.

No long-term credentials required.

---

# Task Execution Role

## What is a Task Execution Role?

Used by ECS itself.

Not by your application.

---

Responsibilities:

- Pull images from ECR
- Send logs to CloudWatch
- Retrieve Secrets Manager values
- Retrieve Parameter Store values

---

# Execution Role Flow

```text
ECS Agent
      ↓
Execution Role
      ↓
AWS Services
```

---

# Example Permissions

```text
ecr:GetAuthorizationToken

logs:CreateLogStream

logs:PutLogEvents
```

---

# Task Role vs Execution Role

| Feature | Task Role | Execution Role |
|----------|------------|----------------|
| Used By | Application | ECS Agent |
| Access S3 | Yes | No |
| Pull Images | No | Yes |
| Write Logs | No | Yes |
| Access Secrets | Optional | Yes |

---

# EC2 Instance Profile

Used only with:

```text
EC2 Launch Type
```

Attached to EC2 instance.

---

# Responsibilities

Examples:

- ECS Agent Registration
- ECR Authentication
- CloudWatch Integration

---

# Architecture

```text
EC2 Instance
      ↓
Instance Profile
      ↓
AWS Services
```

---

# Security Recommendation

Application permissions:

```text
Task Role
```

Infrastructure permissions:

```text
Instance Profile
```

Never combine both.

---

# Secrets Management

Never hardcode:

```text
Passwords
API Keys
Tokens
```

---

# Bad Example

```python
DB_PASSWORD = "mypassword123"
```

Security risk.

---

# AWS Secrets Manager

Store:

- Database Passwords
- API Tokens
- Third-party Credentials

---

# Retrieval Flow

```text
Secrets Manager
      ↓
Execution Role
      ↓
Container
```

Injected securely.

---

# Parameter Store

Useful for:

- Application Configuration
- Feature Flags
- Environment Values

Examples:

```text
/application/env
/application/api-url
```

---

# Secrets Manager vs Parameter Store

| Feature | Secrets Manager | Parameter Store |
|----------|----------------|----------------|
| Encryption | Yes | Yes |
| Rotation | Yes | Limited |
| Cost | Higher | Lower |
| Secrets Storage | Best | Good |

---

# Encryption with KMS

AWS Key Management Service (KMS) protects:

- Secrets
- Storage
- Logs
- Databases

---

# Example

```text
Secrets Manager
       ↓
KMS Encryption
       ↓
Stored Secret
```

---

# ECR Security

ECS commonly pulls images from:

```text
Amazon ECR
```

Required permissions:

```text
ecr:GetAuthorizationToken
ecr:BatchGetImage
```

---

# CloudWatch Permissions

Execution Role typically needs:

```text
logs:CreateLogStream
logs:PutLogEvents
```

For centralized logging.

---

# S3 Access from ECS

Applications frequently access:

- Uploads
- Reports
- Backups

Grant access through:

```text
Task Role
```

Not static credentials.

---

# Example S3 Policy

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "*"
}
```

---

# Security Layers

Production ECS security includes:

```text
IAM
Security Groups
Private Subnets
KMS
Secrets Manager
CloudWatch Monitoring
```

Multiple layers of protection.

---

# Security Best Practices

## Use Least Privilege

Grant only required permissions.

---

## Separate Roles

Use:

```text
Task Role
Execution Role
```

Independently.

---

## Use Secrets Manager

Never store credentials in code.

---

## Rotate Secrets

Reduce long-term exposure.

---

## Enable Encryption

Use KMS wherever possible.

---

## Deploy in Private Subnets

Reduce attack surface.

---

# Common Security Mistakes

## Administrator Access

Problem:

Excessive permissions.

---

## Hardcoded Credentials

Problem:

Credential leakage.

---

## Shared IAM Roles

Problem:

Permission sprawl.

---

## No Encryption

Problem:

Sensitive data exposure.

---

## Public ECS Tasks

Problem:

Increased attack surface.

---

# Common Interview Questions

## What is a Task Role?

Used by application containers.

---

## What is a Task Execution Role?

Used by ECS Agent.

---

## Difference Between Task Role and Execution Role?

Task Role:

Application permissions.

Execution Role:

Infrastructure permissions.

---

## Why Avoid Static Credentials?

Security risk.

Use IAM roles instead.

---

## Why Use Secrets Manager?

Secure secret storage and rotation.

---

## What is Least Privilege?

Grant only required permissions.

---

# Real Production Example

FastAPI Service

Requirements:

- Read from S3
- Send messages to SQS
- Retrieve DB password

Solution:

```text
Task Role
 ├── S3 Access
 └── SQS Access

Execution Role
 ├── ECR Access
 ├── CloudWatch Access
 └── Secrets Manager Access
```

Clean separation of responsibilities.

---

# Senior Engineer Perspective

Security is not a single feature.

It is a collection of controls:

- IAM
- Networking
- Encryption
- Monitoring
- Secret Management

Most ECS security incidents are caused by:

- Excessive IAM permissions
- Hardcoded credentials
- Public exposure

Senior engineers design systems assuming compromise is possible and implement layered defenses.

---

# Key Takeaways

- Task Roles are used by applications.
- Task Execution Roles are used by ECS.
- Instance Profiles are used by EC2 hosts.
- Secrets should be stored in Secrets Manager.
- KMS provides encryption.
- Least privilege is a fundamental security principle.
- IAM is the foundation of ECS security.
