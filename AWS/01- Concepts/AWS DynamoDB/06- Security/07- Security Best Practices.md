# 07 - Security Best Practices

## Overview

Building a secure DynamoDB application is not about enabling a single feature such as encryption or IAM. Instead, security is achieved by combining multiple AWS services, following the principle of **defense in depth**.

A production-grade DynamoDB deployment typically combines:

- IAM
- Fine-Grained Access Control (FGAC)
- AWS KMS
- VPC Endpoints
- CloudTrail
- CloudWatch
- AWS Config
- Security Hub
- GuardDuty
- Backup & Disaster Recovery

Each layer reduces risk and limits the impact of security incidents.

---

# Learning Objectives

After completing this chapter, you'll be able to:

- Design a secure DynamoDB architecture.
- Apply the Principle of Least Privilege.
- Protect data throughout its lifecycle.
- Secure applications running on AWS.
- Detect suspicious activities.
- Build compliant production environments.
- Perform security reviews for DynamoDB deployments.

---

# Defense in Depth

Security should exist at multiple layers.

```text
Users

↓

Authentication

↓

Authorization

↓

Network Security

↓

Encryption

↓

Monitoring

↓

Backup

↓

Recovery
```

If one layer fails, the remaining layers continue protecting the system.

---

# Layer 1 — Identity Security

Every request should originate from a verified identity.

Use:

- IAM Roles
- AWS IAM Identity Center
- Amazon Cognito
- AWS STS

Avoid:

```text
Hardcoded Credentials

↓

Application Source Code
```

Instead:

```text
Application

↓

IAM Role

↓

Temporary Credentials
```

---

# Layer 2 — Authorization

Every identity should have only the permissions it requires.

Example:

```text
Order Service

↓

Orders Table

↓

Read + Write
```

Not:

```text
Order Service

↓

All DynamoDB Tables
```

Follow the Principle of Least Privilege.

---

# Layer 3 — Fine-Grained Access Control

Limit access to specific data.

Example:

```text
Customer

↓

CustomerID = 123

↓

Only Customer 123 Records
```

Never expose entire tables when only a subset of data is required.

---

# Layer 4 — Network Security

Application architecture:

```text
Private Subnet

↓

Gateway VPC Endpoint

↓

DynamoDB
```

Benefits:

- No Internet Gateway
- No NAT dependency
- Private AWS network
- Improved compliance

---

# Layer 5 — Encryption

Protect data:

```text
Client

↓

TLS

↓

DynamoDB

↓

AWS KMS

↓

Encrypted Storage
```

Production systems should use:

- HTTPS
- AWS KMS
- Customer-managed keys when required

---

# Layer 6 — Monitoring

Monitor continuously.

```text
CloudWatch

↓

Metrics

↓

Alarms

↓

Operations Team
```

Watch:

- Throttling
- Latency
- Errors
- Capacity
- Replication

---

# Layer 7 — Auditing

Record every administrative action.

```text
API Call

↓

CloudTrail

↓

Amazon S3

↓

Audit Log
```

Track:

- Table creation
- Table deletion
- IAM changes
- KMS changes
- Backup operations

---

# Layer 8 — Disaster Recovery

Protect against:

- Human error
- Accidental deletion
- Regional outages
- Corrupted data

Architecture:

```text
PITR

+

Backups

+

Global Tables
```

Availability and recoverability should always be planned together.

---

# Secure Production Architecture

```text
                    Users

                       │

             Amazon Cognito

                       │

                IAM Role / STS

                       │

                API Gateway

                       │

               ECS / Lambda

                       │

               Private Subnet

                       │

           Gateway VPC Endpoint

                       │

                  DynamoDB

         ┌─────────────┼─────────────┐

         ▼             ▼             ▼

       KMS        CloudTrail     CloudWatch

         │             │             │

         ▼             ▼             ▼

   Encryption      Audit Logs     Monitoring
```

---

# Secure CI/CD Pipeline

Deployment pipeline:

```text
Developer

↓

GitHub

↓

GitHub Actions

↓

IAM Role

↓

CloudFormation / CDK

↓

DynamoDB
```

Avoid:

- Long-lived AWS access keys
- Manual production deployments
- Shared administrator accounts

---

# Secure Application Design

Applications should:

- Validate all inputs.
- Never trust client requests.
- Use parameterized PartiQL statements.
- Handle authorization failures gracefully.
- Log security events.
- Avoid exposing internal errors.

---

# Secrets Management

Never store secrets in:

- Source code
- Git repositories
- Docker images
- Configuration files

Use:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

Applications should retrieve secrets at runtime.

---

# Logging Best Practices

Log:

- Authentication failures
- Authorization failures
- Unexpected exceptions
- High error rates
- Configuration changes

Do **not** log:

- Passwords
- Access keys
- Session tokens
- Personally identifiable information (PII)
- Encryption keys

---

# Operational Security Checklist

Before deploying a production table, verify:

- IAM Roles are used.
- Least-privilege policies are applied.
- Encryption is enabled.
- Gateway VPC Endpoints are configured.
- CloudTrail is enabled.
- CloudWatch alarms are configured.
- PITR is enabled.
- Backups are scheduled.
- KMS permissions are reviewed.
- Access has been tested.

---

# Security Review Checklist

Questions every engineer should ask:

- Who can read this table?
- Who can modify this table?
- Are credentials temporary?
- Is data encrypted?
- Can access be audited?
- Can deleted data be recovered?
- Is private networking used?
- Are alarms configured?
- Is compliance documented?

If any answer is "No," the deployment should be reviewed.

---

# Common Security Mistakes

## Using AdministratorAccess

Poor:

```text
Lambda

↓

AdministratorAccess
```

Better:

```text
Lambda

↓

OrdersRole

↓

Only Required Permissions
```

---

## Hardcoding Credentials

Never:

```python
AWS_ACCESS_KEY_ID="AKIA..."
```

Always prefer IAM Roles.

---

## Public Compute Resources

Avoid unnecessary public subnets for backend workloads.

Prefer:

```text
Private Subnet

↓

Gateway Endpoint

↓

DynamoDB
```

---

## Ignoring Monitoring

Security without monitoring is incomplete.

Enable:

- CloudWatch
- CloudTrail
- GuardDuty
- Security Hub

---

## Forgetting Disaster Recovery

Security includes:

- Prevention
- Detection
- Recovery

Recovery planning is just as important as access control.

---

# Production Considerations

Enterprise organizations typically standardize on:

```text
AWS Organizations

↓

IAM Identity Center

↓

Service Control Policies (SCPs)

↓

Customer Managed KMS Keys

↓

Private VPCs

↓

CloudTrail

↓

Security Hub

↓

GuardDuty

↓

AWS Config

↓

DynamoDB
```

This architecture provides centralized governance, continuous monitoring, and strong operational security.

---

# Interview Notes

A common interview question is:

> **How would you secure a production DynamoDB application?**

Use IAM Roles with least-privilege policies, Fine-Grained Access Control, KMS encryption, Gateway VPC Endpoints, CloudTrail auditing, CloudWatch monitoring, backups, PITR, and continuous compliance monitoring through AWS Config and Security Hub.

---

Another common question is:

> **What is defense in depth?**

Defense in depth is a security strategy that uses multiple independent layers—identity, authorization, networking, encryption, monitoring, and recovery—so that failure of one control does not compromise the entire system.

---

Another common question is:

> **Why are IAM Roles preferred over access keys?**

IAM Roles provide temporary credentials that rotate automatically, reducing the risk of credential leakage and eliminating the need to store secrets within applications.

---

Another common question is:

> **What AWS services are commonly used alongside DynamoDB for security?**

IAM, AWS KMS, Amazon Cognito, CloudTrail, CloudWatch, AWS Config, Security Hub, GuardDuty, AWS Backup, and VPC Endpoints.

---

# Key Takeaways

- Security is achieved through multiple complementary controls rather than a single feature.
- Use IAM Roles, least-privilege policies, and Fine-Grained Access Control to secure access.
- Protect data with TLS, AWS KMS, and private networking through Gateway VPC Endpoints.
- Enable CloudTrail and CloudWatch for auditing, monitoring, and incident response.
- Combine PITR and backups with preventive security controls to ensure resilience.
- A production-ready DynamoDB deployment should follow a defense-in-depth strategy with continuous monitoring and regular security reviews.