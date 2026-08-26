# 22 - Security and Encryption

## Overview

Security is one of the most critical aspects of any production database.

A DynamoDB table may contain:

- Customer information
- Financial transactions
- Authentication tokens
- Medical records
- Personally Identifiable Information (PII)
- Business-critical data

A database that scales to millions of requests per second is of little value if unauthorized users can access or modify its contents.

DynamoDB follows AWS's **shared responsibility model**:

- **AWS** is responsible for securing the infrastructure, hardware, networking, and managed service.
- **Customers** are responsible for securing their data, identities, permissions, encryption keys, and application access.

Understanding DynamoDB security means understanding how AWS layers multiple security controls together rather than relying on a single mechanism.

---

# DynamoDB Security Layers

A production DynamoDB deployment is protected by several independent layers.

```text
                   Application

                         │

                         ▼

                IAM Authentication

                         │

                         ▼

             IAM Authorization Policies

                         │

                         ▼

               TLS Encryption in Transit

                         │

                         ▼

                  DynamoDB Service

                         │

                         ▼

             KMS Encryption at Rest

                         │

                         ▼

               Physical AWS Storage
```

Each layer protects against a different type of attack.

---

# Authentication

Before a client can access DynamoDB, AWS must verify **who the caller is**.

This process is called **authentication**.

Common authentication methods include:

- IAM Users
- IAM Roles
- EC2 Instance Profiles
- ECS Task Roles
- Lambda Execution Roles
- AWS STS Temporary Credentials
- Federated Identity (AWS IAM Identity Center)

Example:

```text
Application

↓

IAM Role

↓

Temporary Credentials

↓

DynamoDB
```

Production applications should almost always use **IAM Roles** instead of long-lived access keys.

---

# Authorization

After authentication succeeds, AWS evaluates:

> **What is this identity allowed to do?**

Authorization is controlled through **IAM Policies**.

Example policy:

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:Query"
  ],
  "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/Orders"
}
```

This policy allows:

- GetItem
- Query

But denies:

- DeleteItem
- Scan
- UpdateItem

unless explicitly granted.

---

# Principle of Least Privilege

One of AWS's core security principles is:

> Grant only the permissions that are absolutely necessary.

Bad example:

```text
Allow

dynamodb:*
```

Good example:

```text
Allow

GetItem

Query
```

Applications should receive only the permissions they require.

---

# Resource-Level Permissions

IAM policies can restrict access to specific tables.

Example:

```text
Application A

↓

Orders Table
```

Application A cannot access:

```text
Customers Table
```

unless explicitly permitted.

This prevents accidental or malicious access across workloads.

---

# Fine-Grained Access Control (FGAC)

Sometimes restricting access to an entire table is insufficient.

Example:

A multi-tenant SaaS platform stores data for thousands of customers.

```text
Tenant A

Tenant B

Tenant C
```

All tenants share the same DynamoDB table.

FGAC allows policies such as:

```text
User

↓

Can Read

↓

Only Items

Where

TenantId = "TenantA"
```

This is commonly implemented using IAM policy conditions with DynamoDB partition keys.

---

# Encryption at Rest

All modern DynamoDB tables support **encryption at rest**.

```text
Application

↓

Write Item

↓

Encrypt

↓

Store on Disk
```

If physical storage devices are stolen or compromised, the stored data remains unreadable without the encryption keys.

---

# AWS Key Management Service (KMS)

DynamoDB uses **AWS KMS** to manage encryption keys.

Three common options exist.

### AWS Owned Keys

```text
AWS

↓

Manages Everything
```

Simplest option.

Minimal administrative overhead.

---

### AWS Managed Keys

```text
AWS

↓

Creates Key

↓

Customer Uses
```

Provides more visibility while AWS manages key rotation.

---

### Customer Managed Keys (CMKs)

```text
Customer

↓

Owns KMS Key

↓

Controls Policies

↓

Controls Rotation
```

Provides maximum control.

Often required for:

- Financial institutions
- Healthcare
- Government
- Compliance-driven environments

---

# Encryption in Transit

Data should also be protected while traveling across the network.

```text
Application

↓

TLS

↓

DynamoDB
```

All communication with DynamoDB occurs over HTTPS using TLS.

This prevents attackers from reading network traffic.

---

# VPC Endpoints (PrivateLink)

Normally:

```text
Application

↓

Internet

↓

DynamoDB
```

Although encrypted, traffic still traverses the public AWS endpoint.

With a VPC Endpoint:

```text
Application

↓

Private AWS Network

↓

DynamoDB
```

Traffic never leaves the AWS backbone.

Benefits include:

- Lower attack surface
- Private connectivity
- Compliance requirements
- Reduced exposure to the public internet

---

# CloudTrail Auditing

Every API call to DynamoDB can be recorded using AWS CloudTrail.

Example:

```text
User

↓

DeleteItem

↓

CloudTrail Log
```

CloudTrail records:

- Who performed the action
- When it occurred
- Source IP
- AWS Region
- API operation
- Request parameters

These logs are essential for:

- Security investigations
- Compliance
- Auditing
- Incident response

---

# Monitoring with CloudWatch

CloudWatch complements CloudTrail.

CloudWatch focuses on:

- Performance
- Availability
- Capacity
- Operational metrics

CloudTrail focuses on:

- API activity
- User actions
- Security auditing

Both services should be enabled in production.

---

# Cross-Account Access

Organizations often operate multiple AWS accounts.

Example:

```text
Account A

↓

Analytics
```

```text
Account B

↓

Production Database
```

Instead of sharing credentials:

```text
AssumeRole

↓

Temporary Credentials

↓

Access DynamoDB
```

AWS STS enables secure cross-account access.

---

# Temporary Credentials

Long-lived access keys present significant security risks.

Preferred approach:

```text
IAM Role

↓

Temporary Credentials

↓

Automatic Rotation
```

Benefits:

- Short-lived
- Automatically rotated
- No embedded secrets
- Reduced credential leakage risk

This is the standard approach for:

- Lambda
- ECS
- EC2
- EKS

---

# Data Protection Strategies

Production systems commonly combine multiple security mechanisms.

```text
IAM

+

KMS

+

TLS

+

CloudTrail

+

CloudWatch

+

VPC Endpoint
```

Security is achieved through defense in depth.

---

# Common Security Architecture

```text
Users

↓

API Gateway

↓

Lambda (IAM Role)

↓

VPC Endpoint

↓

DynamoDB

↓

Encrypted with KMS

↓

CloudTrail Logs
```

Every request is:

- Authenticated
- Authorized
- Encrypted
- Audited

---

# Best Practices

- Use IAM Roles instead of access keys.
- Apply the principle of least privilege.
- Enable encryption at rest.
- Use customer-managed KMS keys when compliance requires them.
- Always communicate using HTTPS/TLS.
- Enable CloudTrail in every AWS account.
- Use VPC Endpoints for production workloads.
- Rotate secrets automatically.
- Regularly review IAM policies.
- Enable CloudWatch alarms for suspicious activity.

---

# Common Mistakes

## Using AdministratorAccess Everywhere

Granting full permissions increases the blast radius of compromised credentials.

---

## Embedding AWS Credentials in Code

Never hardcode:

```text
AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY
```

Use IAM Roles instead.

---

## Ignoring CloudTrail

Without audit logs, investigating security incidents becomes significantly more difficult.

---

## Overly Broad IAM Policies

Avoid:

```text
Action

*

Resource

*
```

Restrict permissions whenever possible.

---

## Assuming Encryption Alone Is Enough

Encryption protects stored data.

It does not replace:

- Authentication
- Authorization
- Auditing
- Monitoring

Security requires multiple layers.

---

# Real-World Example

A payment processing service stores transaction records.

Architecture:

```text
API Gateway

↓

Lambda

↓

IAM Role

↓

Private VPC Endpoint

↓

DynamoDB

↓

Encrypted Using Customer Managed KMS Key

↓

CloudTrail Audit Logs
```

Even if a Lambda function is compromised, its IAM role limits the actions it can perform, all requests are audited, and the underlying data remains encrypted.

---

# Architecture Perspective

A secure production deployment typically looks like:

```text
Client

↓

Amazon Cognito / IAM

↓

API Gateway

↓

Lambda / ECS

↓

IAM Role

↓

VPC Endpoint

↓

DynamoDB

↓

KMS Encryption

↓

AWS Managed Storage

────────────────────────────

CloudTrail

↓

Security Audit

────────────────────────────

CloudWatch

↓

Monitoring & Alerts
```

Each AWS service contributes to a layered security model that protects identities, data, and operational visibility.

---

# Interview Notes

A common interview question is:

> **How would you secure a production DynamoDB table?**

A senior engineer would typically recommend:

- IAM Roles instead of access keys
- Least privilege IAM policies
- Encryption at rest using AWS KMS
- TLS for encryption in transit
- CloudTrail for auditing
- CloudWatch for monitoring
- VPC Endpoints for private connectivity
- Fine-Grained Access Control for multi-tenant applications
- Regular IAM policy reviews and key rotation

Another common question is:

> **What is the difference between authentication and authorization?**

Authentication verifies **who you are**.

Authorization determines **what you are allowed to do**.

Both are required before a request can successfully access DynamoDB.

---

# Key Takeaways

- DynamoDB security is built on multiple layers rather than a single feature.
- IAM provides authentication and authorization.
- Least privilege is the foundation of secure AWS access control.
- DynamoDB encrypts data at rest using AWS KMS and protects data in transit using TLS.
- VPC Endpoints allow private access without traversing the public internet.
- CloudTrail records every API action for auditing and compliance.
- CloudWatch provides operational monitoring and alerting.
- Production-grade security combines IAM, KMS, TLS, CloudTrail, CloudWatch, and VPC Endpoints into a defense-in-depth strategy.