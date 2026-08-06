# 03- Lambda Security

# Overview

Security is one of the most critical aspects of building production-grade AWS Lambda applications. Since Lambda functions often interact with databases, object storage, messaging systems, APIs, and other AWS services, improper security configurations can expose sensitive data, allow privilege escalation, or compromise an entire cloud environment.

AWS follows a **Shared Responsibility Model**, where AWS secures the underlying infrastructure, while customers are responsible for securing their code, IAM permissions, secrets, networking, and data.

Senior backend engineers should design Lambda functions following the principles of **least privilege**, **defense in depth**, and **zero trust**.

---

# AWS Shared Responsibility Model

```
AWS Responsibilities

↓

Physical Security

Networking

Compute Infrastructure

Runtime Patching

Availability

----------------------------

Customer Responsibilities

↓

IAM

Application Code

Secrets

Encryption

Networking Configuration

Data Protection
```

Security is a shared responsibility.

---

# Security Layers

A production Lambda function should be protected using multiple security layers.

```
User

↓

Authentication

↓

Authorization

↓

API Gateway

↓

Lambda

↓

IAM Role

↓

AWS Resources

↓

Encryption

↓

Monitoring
```

---

# Identity and Access Management (IAM)

Every Lambda function executes using an **IAM Execution Role**.

```
Lambda

↓

IAM Role

↓

AWS Services
```

The execution role determines what AWS resources the function can access.

---

# Principle of Least Privilege

Grant only the permissions required.

Good

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject"
  ],
  "Resource": [
    "arn:aws:s3:::documents/*"
  ]
}
```

Bad

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

Never use administrator permissions for production Lambda functions.

---

# Execution Role vs Resource Policy

Execution Role

```
Lambda

↓

Access AWS Resources
```

Resource Policy

```
Other AWS Services

↓

Invoke Lambda
```

Example:

- API Gateway invokes Lambda.
- Lambda reads from S3.

These require different permission models.

---

# Secrets Management

Never hardcode:

- Database passwords
- API Keys
- Access Tokens
- Private Keys

Instead use:

```
AWS Secrets Manager

↓

Lambda

↓

Retrieve Secret
```

or

```
AWS Systems Manager Parameter Store
```

---

# Environment Variables

Environment variables should contain:

- Configuration
- Region
- Feature Flags
- Log Levels

Avoid storing secrets here.

Example

```
LOG_LEVEL=INFO

REGION=us-east-1

ENV=production
```

---

# Encryption

## Encryption at Rest

Sensitive resources should be encrypted.

Examples

```
S3

↓

KMS

↓

Encrypted Objects
```

```
EFS

↓

KMS

↓

Encrypted Files
```

---

## Encryption in Transit

Always use TLS.

```
Lambda

↓

HTTPS

↓

External API
```

Never send credentials over HTTP.

---

# AWS KMS

AWS Key Management Service protects encryption keys.

Common integrations:

- Secrets Manager
- Environment Variables
- S3
- EFS
- DynamoDB

---

# VPC Security

When Lambda accesses private resources:

```
Lambda

↓

Private Subnet

↓

Security Group

↓

Aurora
```

Best Practices

- Private subnets
- Security Groups
- VPC Endpoints
- Least network access

---

# Security Groups

Security Groups control network traffic.

Example

```
Lambda SG

↓

Port 5432

↓

Aurora SG
```

Avoid broad CIDR rules.

---

# API Authentication

Common authentication methods:

- IAM Authentication
- JWT
- Amazon Cognito
- Lambda Authorizers
- OAuth 2.0

Typical flow

```
Client

↓

API Gateway

↓

Authorizer

↓

Lambda
```

---

# Authorization

Authentication verifies identity.

Authorization determines permissions.

```
Authenticated User

↓

Role Check

↓

Permission

↓

Execute Lambda
```

---

# Secure External API Calls

Store API credentials securely.

```
Secrets Manager

↓

Lambda

↓

Stripe API
```

Avoid embedding secrets inside the application code.

---

# Logging Security

Avoid logging:

- Passwords
- Tokens
- JWTs
- Credit Card Numbers
- Personal Information

Good

```python
logger.info(
    "Order Created",
    extra={
        "order_id": order_id
    }
)
```

Bad

```python
logger.info(event)
```

---

# CloudTrail

CloudTrail records Lambda management events.

Examples

- Create Function
- Delete Function
- Update Configuration
- IAM Changes

Useful for:

- Auditing
- Compliance
- Incident Investigation

---

# CloudWatch

Monitor:

- Errors
- Invocations
- Duration
- Throttles

Configure alarms for unusual activity.

---

# AWS X-Ray

Use X-Ray to:

- Detect failures
- Analyze latency
- Trace requests
- Debug production issues

---

# Dependency Security

Third-party packages introduce risk.

Best Practices

- Remove unused libraries
- Update dependencies
- Scan for vulnerabilities
- Use trusted sources

---

# Container Image Security

If using Lambda Container Images:

- Use AWS base images
- Scan ECR repositories
- Minimize image size
- Remove build tools
- Rebuild regularly

---

# Secure Deployment Pipeline

Typical pipeline

```
GitHub

↓

CI

↓

Security Scan

↓

Tests

↓

Deploy

↓

Lambda
```

Automate security validation before deployment.

---

# Cross-Account Access

Sometimes Lambda must access resources in another AWS account.

Architecture

```
Lambda

↓

Assume Role

↓

Other AWS Account
```

Avoid sharing long-term credentials.

---

# Common Security Mistakes

## AdministratorAccess

Never assign:

```
AdministratorAccess
```

to Lambda execution roles.

---

## Hardcoded Credentials

Bad

```python
password = "admin123"
```

Use Secrets Manager instead.

---

## Public Databases

Avoid

```
Lambda

↓

Public RDS
```

Prefer

```
Lambda

↓

Private Subnet

↓

RDS Proxy

↓

Aurora
```

---

## Logging Sensitive Data

Do not log:

- Passwords
- API Keys
- Access Tokens
- Customer Information

---

## Excessive Permissions

Review IAM policies regularly.

Grant only required actions.

---

# Security Checklist

Before production deployment:

- [ ] IAM follows least privilege
- [ ] Secrets stored in Secrets Manager
- [ ] Encryption enabled
- [ ] TLS used everywhere
- [ ] CloudTrail enabled
- [ ] CloudWatch monitoring configured
- [ ] X-Ray enabled where appropriate
- [ ] Dependencies updated
- [ ] Security Groups reviewed
- [ ] VPC configured correctly

---

# Real-World Secure Architecture

```
Users

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

├── IAM Role

├── Secrets Manager

├── RDS Proxy

├── CloudWatch

├── X-Ray

└── CloudTrail

↓

Aurora
```

This architecture combines authentication, authorization, encryption, monitoring, and auditing.

---

# Security Best Practices

✅ Apply the Principle of Least Privilege.

✅ Store secrets in AWS Secrets Manager.

✅ Encrypt data at rest using AWS KMS.

✅ Use HTTPS for all communication.

✅ Keep Lambda functions inside private subnets when accessing private resources.

✅ Regularly rotate credentials.

✅ Enable CloudTrail and CloudWatch monitoring.

✅ Keep dependencies updated.

✅ Review IAM policies periodically.

---

# Senior Backend Engineering Perspective

Security is not a single feature—it is a continuous process integrated into every stage of application development and operations.

Senior engineers design Lambda applications assuming that every component may eventually be targeted. They rely on layered defenses, automated security controls, strong IAM boundaries, encrypted communication, secure secret management, and comprehensive monitoring to reduce risk.

Rather than trusting any single control, production systems combine identity, networking, encryption, logging, and continuous auditing to create a resilient security posture.

---

# Key Takeaways

- AWS Lambda security follows the Shared Responsibility Model.
- IAM execution roles should always follow the Principle of Least Privilege.
- Secrets must be stored in AWS Secrets Manager or Parameter Store rather than application code.
- Encryption, secure networking, monitoring, and auditing are essential components of production serverless applications.
- Strong security is achieved through multiple layers of protection rather than a single mechanism.