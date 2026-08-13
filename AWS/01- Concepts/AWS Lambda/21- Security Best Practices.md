# 21- Lambda Security Best Practices

# Introduction

Security is one of the most critical aspects of any serverless application. While AWS manages the underlying infrastructure, customers remain responsible for securing:

- Lambda code
- IAM permissions
- Secrets
- Network access
- Dependencies
- Data encryption
- API security

This follows the **AWS Shared Responsibility Model**.

```
AWS

↓

Infrastructure
Hypervisor
Hardware
Networking

-------------------------

Customer

↓

Code

IAM

Secrets

Environment Variables

Dependencies

Application Security
```

A Lambda function is only as secure as the permissions granted to it.

---

# Shared Responsibility Model

AWS is responsible for:

- Physical security
- Compute infrastructure
- Firecracker microVM isolation
- Runtime infrastructure
- Availability

Customers are responsible for:

- IAM Roles
- Resource Policies
- Encryption
- Secrets
- Source Code
- Dependencies
- Business Logic

---

# Principle of Least Privilege

The most important Lambda security principle is:

> **Grant only the permissions that are absolutely necessary.**

Bad Policy:

```json
{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
}
```

Good Policy:

```json
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject"
    ],
    "Resource": [
        "arn:aws:s3:::orders-bucket/*"
    ]
}
```

---

# IAM Execution Role

Every Lambda executes using an IAM Role.

```
Lambda

↓

IAM Role

↓

AWS Services
```

The role determines everything the function can access.

---

# IAM Role vs Resource Policy

Execution Role

```
What Lambda can access
```

Resource Policy

```
Who can invoke Lambda
```

These are completely different concepts.

---

# Example Architecture

```
API Gateway

↓

Lambda

↓

IAM Role

↓

DynamoDB

↓

Secrets Manager

↓

CloudWatch
```

Each service requires explicit permissions.

---

# Never Use AdministratorAccess

Bad Practice:

```
Lambda Role

↓

AdministratorAccess
```

This grants unnecessary permissions.

Instead:

Grant only:

- Read bucket
- Write logs
- Read secret
- Query database

Nothing more.

---

# Secure Environment Variables

Environment Variables are encrypted using AWS KMS.

```
Environment Variables

↓

KMS

↓

Lambda
```

However,

Do **not** store:

- Database passwords
- API Keys
- OAuth Secrets

Use Secrets Manager instead.

---

# AWS Secrets Manager

Recommended pattern:

```
Lambda

↓

Secrets Manager

↓

Retrieve Secret

↓

Memory Cache

↓

Business Logic
```

Benefits:

- Automatic rotation
- Encryption
- Auditing
- Access control

---

# Systems Manager Parameter Store

Useful for:

- Feature flags
- Configuration
- Non-sensitive settings
- Secure Strings

```
Lambda

↓

Parameter Store

↓

Configuration
```

---

# Encryption

Data should be encrypted:

### At Rest

Examples:

- S3
- EFS
- Environment Variables
- DynamoDB

### In Transit

Use:

```
HTTPS

TLS 1.2+

Private VPC Endpoints
```

---

# VPC Security

If Lambda runs inside a VPC:

```
Lambda

↓

Private Subnet

↓

Security Group

↓

RDS
```

Never place production databases inside public subnets.

---

# Security Groups

Example:

```
Lambda SG

↓

Allows

↓

TCP 5432

↓

RDS SG
```

Avoid:

```
0.0.0.0/0
```

for internal communication.

---

# Resource-Based Policies

Resource policies define who may invoke Lambda.

Example:

```
S3

↓

Invoke Lambda
```

Only authorized services should be allowed.

---

# API Gateway Security

Typical architecture:

```
Internet

↓

CloudFront

↓

WAF

↓

API Gateway

↓

Lambda
```

Additional protection includes:

- Authentication
- Authorization
- Rate limiting

---

# Validate Input

Never trust incoming data.

Always validate:

- JSON schema
- Data types
- Length
- Required fields

Example:

```
Client

↓

Validation

↓

Business Logic
```

Never execute unvalidated input.

---

# Dependency Security

Lambda packages often contain dozens of third-party libraries.

Regularly scan dependencies.

Popular tools:

- pip-audit
- Safety
- Dependabot
- Snyk

---

# Keep Runtime Updated

AWS regularly introduces new managed runtimes.

Example:

Instead of:

```
Python 3.8
```

Upgrade to:

```
Python 3.13
```

Benefits:

- Security patches
- Performance improvements
- Longer support lifecycle

---

# Code Signing

AWS supports Lambda Code Signing.

```
Developer

↓

Sign Package

↓

Upload

↓

Lambda

↓

Verify Signature
```

Only trusted packages are deployed.

---

# Logging Security

Never log:

- Passwords
- Access Tokens
- JWTs
- API Keys
- Credit Card Numbers

Instead:

```
User ID

Transaction ID

Correlation ID
```

---

# Temporary Credentials

Lambda automatically receives temporary AWS credentials.

```
IAM Role

↓

STS

↓

Temporary Credentials

↓

Lambda
```

Never embed long-term AWS credentials inside code.

---

# Protect Against SSRF

If Lambda performs outbound HTTP requests:

Validate:

- URL
- Domain
- Protocol

Prevent:

```
http://169.254.169.254
```

or other unintended internal endpoints.

---

# Timeouts

Always configure sensible timeouts.

Bad:

```
900 Seconds

For Small API
```

Better:

```
5 Seconds

10 Seconds

30 Seconds
```

depending on workload.

---

# Denial of Wallet

Unlike traditional servers,

Attackers can generate excessive Lambda invocations.

Mitigation:

- AWS WAF
- API Gateway throttling
- Usage plans
- Authentication
- CloudFront caching

---

# Network Isolation

Private architecture:

```
Internet

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Private Subnet

↓

RDS
```

No public database exposure.

---

# Monitor Security Events

Use:

- CloudTrail
- GuardDuty
- Security Hub
- CloudWatch
- AWS Config

Together they provide:

- Auditing
- Threat detection
- Compliance monitoring

---

# Common Vulnerabilities

### Excessive IAM Permissions

Most common mistake.

---

### Hardcoded Secrets

Never commit:

```
AWS_SECRET_ACCESS_KEY

DATABASE_PASSWORD
```

---

### Unvalidated Input

May result in:

- Injection attacks
- Data corruption
- Application crashes

---

### Logging Sensitive Data

Logs often outlive application data.

Treat logs as sensitive assets.

---

# Security Checklist

✅ Least Privilege IAM

✅ Secrets Manager

✅ Parameter Store

✅ KMS Encryption

✅ HTTPS Everywhere

✅ VPC Isolation

✅ Security Groups

✅ Dependency Scanning

✅ Input Validation

✅ Logging Hygiene

✅ CloudTrail

✅ Code Signing

---

# Real-World Secure Architecture

```
Internet

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Cognito

↓

Lambda

↓

IAM Role

↓

Secrets Manager

↓

Private RDS

↓

CloudWatch

↓

CloudTrail
```

Every component contributes to the overall security posture.

---

# Senior Backend Engineering Perspective

Security in serverless applications extends far beyond writing secure code. It requires carefully controlling permissions, isolating resources, encrypting data, managing secrets, validating inputs, and continuously monitoring the environment.

A well-designed Lambda platform follows a **defense-in-depth** strategy:

- IAM enforces least privilege.
- Secrets Manager protects credentials.
- KMS encrypts sensitive data.
- VPCs isolate private resources.
- CloudTrail records every administrative action.
- WAF and API Gateway defend against external threats.
- Dependency scanning and code signing reduce software supply chain risks.

The strongest serverless architectures assume that failures and attacks will occur and are designed to minimize their impact through layered security controls.

---

# Interview Questions

### Beginner

- What is the Lambda execution role?
- Why shouldn't you store passwords in environment variables?
- What is the principle of least privilege?

### Intermediate

- What is the difference between an execution role and a resource-based policy?
- How does Secrets Manager differ from Parameter Store?
- Why should Lambda use temporary credentials?

### Senior

- How would you secure a payment-processing Lambda function?
- How would you implement defense-in-depth for a serverless application?
- Explain how IAM, KMS, WAF, CloudTrail, and Secrets Manager work together.
- How would you protect Lambda from Denial-of-Wallet attacks?

---

# Key Takeaways

- Security in AWS Lambda is governed by the Shared Responsibility Model.
- Always follow the Principle of Least Privilege when designing IAM roles.
- Store secrets in AWS Secrets Manager rather than environment variables.
- Protect private resources using VPCs, Security Groups, and encryption.
- Combine IAM, KMS, WAF, CloudTrail, dependency scanning, and monitoring to build secure, production-ready serverless applications.