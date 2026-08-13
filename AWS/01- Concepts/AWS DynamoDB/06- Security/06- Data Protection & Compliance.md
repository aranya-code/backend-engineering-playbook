# 06 - Data Protection & Compliance

## Overview

For many organizations, securing a DynamoDB table is only part of the challenge. Equally important is ensuring that data handling complies with regulatory, legal, and organizational requirements.

Industries such as:

- Banking
- Healthcare
- Government
- Insurance
- E-commerce
- Telecommunications

must demonstrate that customer data is:

- Protected
- Auditable
- Encrypted
- Recoverable
- Properly retained
- Properly deleted

Amazon DynamoDB provides multiple features that help organizations build compliant systems.

However, compliance is **not** a single AWS feature—it is achieved by combining multiple AWS services into a secure architecture.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Shared Responsibility Model
- Data classification
- Encryption requirements
- Access control
- Audit logging
- Data retention
- Compliance frameworks
- Production compliance architectures

---

# AWS Shared Responsibility Model

AWS secures the infrastructure.

Customers secure their data.

```text
AWS

↓

Physical Data Centers

Networking

Hardware

Hypervisor

────────────

Customer

↓

IAM

Encryption

Applications

Data

Policies
```

AWS is responsible **for** the cloud.

Customers are responsible **in** the cloud.

---

# Data Classification

Not all data requires the same level of protection.

Typical classifications:

```text
Public

↓

Internal

↓

Confidential

↓

Highly Confidential
```

Example:

| Data | Classification |
|-------|----------------|
| Product Catalog | Public |
| Employee Directory | Internal |
| Customer Orders | Confidential |
| Credit Card Data | Highly Confidential |

Security controls should increase as sensitivity increases.

---

# Personally Identifiable Information (PII)

Examples include:

- Name
- Email
- Phone Number
- Passport Number
- National ID
- Address

Applications should minimize storage of PII whenever possible.

Example:

Poor:

```text
Customer

↓

Name

Address

Passport

Credit Card
```

Better:

```text
Customer

↓

CustomerID

↓

Sensitive Data Stored Elsewhere
```

---

# Data Encryption Strategy

Production architecture should include:

```text
TLS

+

KMS

+

IAM

+

CloudTrail
```

Layers:

```text
Client

↓

HTTPS

↓

DynamoDB

↓

KMS Encryption

↓

Encrypted Storage
```

Defense in depth is preferred over relying on a single security mechanism.

---

# Data Retention

Organizations often have legal retention requirements.

Example:

```text
Audit Logs

↓

7 Years
```

Customer sessions:

```text
24 Hours
```

Temporary OTPs:

```text
5 Minutes
```

Retention policies should align with business and regulatory requirements.

---

# Data Lifecycle

Typical lifecycle:

```text
Create

↓

Use

↓

Archive

↓

Delete
```

DynamoDB features supporting lifecycle management include:

- TTL
- Export to Amazon S3
- PITR
- Backup & Restore

---

# Secure Deletion

Deleting an item is not always sufficient.

Example workflow:

```text
Expired Record

↓

TTL

↓

Delete

↓

CloudTrail Log

↓

Audit Complete
```

Deletion should be traceable.

---

# Audit Logging

Every important operation should be auditable.

Examples:

```text
CreateTable

DeleteTable

UpdateTable

IAM Changes

KMS Changes
```

CloudTrail records these events.

---

# Compliance Architecture

```text
Application

↓

IAM

↓

DynamoDB

↓

CloudTrail

↓

Amazon S3

↓

Athena

↓

Compliance Reports
```

Auditors can investigate historical activity without accessing production systems.

---

# Regulatory Frameworks

## GDPR

Applies primarily to organizations handling personal data of individuals in the European Union.

Requirements include:

- Protect personal data
- Limit access
- Support deletion requests
- Audit access
- Secure storage

Relevant DynamoDB features:

- IAM
- KMS
- CloudTrail
- TTL
- Backups

---

## HIPAA

Healthcare organizations must protect medical records.

Architecture:

```text
Doctors

↓

IAM

↓

Encrypted DynamoDB

↓

CloudTrail
```

Important controls:

- Encryption
- Audit logging
- Least privilege
- Access monitoring

---

## PCI DSS

Organizations processing payment card information should implement:

- Encryption
- IAM
- Logging
- Monitoring
- Network isolation

DynamoDB should avoid storing payment information unless required.

Prefer using payment providers that tokenize card data.

---

## SOC 2

SOC 2 focuses on:

- Security
- Availability
- Confidentiality
- Processing integrity

CloudTrail and CloudWatch are commonly used to demonstrate operational controls.

---

## ISO 27001

Common security controls include:

- Risk management
- Encryption
- Logging
- Access control
- Incident response

DynamoDB integrates well into ISO-compliant environments.

---

# Data Residency

Some regulations require data to remain in a specific country or region.

Example:

```text
EU Customers

↓

EU AWS Region
```

Global Tables should only replicate into approved Regions.

---

# Least Privilege

Applications should access only necessary data.

Example:

```text
Customer Service

↓

Orders

────────────

Finance

↓

Payments
```

Separate IAM roles improve security.

---

# Multi-Tenant Isolation

SaaS applications should isolate tenants.

Architecture:

```text
Tenant A

↓

Partition A

────────────

Tenant B

↓

Partition B
```

Combine:

- FGAC
- IAM
- Tenant-aware partition keys

---

# Compliance Monitoring

Continuously monitor:

- CloudTrail
- CloudWatch
- AWS Config
- Security Hub
- GuardDuty

Architecture:

```text
AWS Resources

↓

Monitoring

↓

Compliance Dashboard
```

Compliance should be continuous, not periodic.

---

# Incident Response

Suppose unauthorized access occurs.

Workflow:

```text
Alert

↓

CloudTrail

↓

Security Team

↓

Investigate

↓

Contain

↓

Recover
```

Prepared incident response procedures reduce recovery time.

---

# Production Security Architecture

```text
Users

↓

Amazon Cognito

↓

IAM Roles

↓

Private VPC

↓

Gateway Endpoint

↓

DynamoDB

↓

KMS Encryption

↓

CloudTrail

↓

CloudWatch

↓

Security Hub
```

Every layer contributes to compliance.

---

# Best Practices

- Encrypt every production table.
- Use customer-managed KMS keys where regulations require them.
- Enable CloudTrail organization-wide.
- Store audit logs in immutable storage.
- Apply least-privilege IAM policies.
- Separate production and development environments.
- Use TTL for temporary records.
- Regularly review access permissions.
- Test disaster recovery procedures.
- Document security controls.

---

# Common Mistakes

## Treating Compliance as an AWS Feature

Compliance depends on architecture, policies, and operational processes—not just AWS services.

---

## Over-Permissive IAM Policies

Poor:

```text
AdministratorAccess
```

Better:

```text
Specific Role

↓

Specific Table

↓

Specific Actions
```

---

## Ignoring Data Residency

Global replication may violate regional regulations if data is copied into unauthorized Regions.

---

## Not Auditing Administrative Actions

Changes to:

- IAM
- KMS
- Table configuration

should always be logged and reviewed.

---

## Keeping Data Forever

Unused data increases:

- Storage costs
- Security risk
- Compliance burden

Use TTL, archival, and retention policies.

---

# Production Considerations

Enterprise environments commonly implement:

```text
AWS Organizations

↓

Control Tower

↓

IAM Identity Center

↓

KMS

↓

CloudTrail

↓

AWS Config

↓

Security Hub

↓

GuardDuty

↓

DynamoDB
```

This architecture provides:

- Strong identity management
- Continuous compliance monitoring
- Centralized auditing
- Automated security findings
- Organization-wide governance

---

# Interview Notes

A common interview question is:

> **Is DynamoDB compliant with regulations such as GDPR or HIPAA?**

DynamoDB provides features that support compliance, including encryption, IAM, CloudTrail, backups, and monitoring. Whether an application is compliant depends on how these features are implemented and how the overall system is designed.

---

Another common question is:

> **Who is responsible for securing data in DynamoDB?**

AWS is responsible for the underlying infrastructure, while customers are responsible for configuring IAM, encryption, network security, monitoring, backups, and compliance controls.

---

Another common question is:

> **How can you protect sensitive customer data in DynamoDB?**

Use encryption with AWS KMS, least-privilege IAM policies, Fine-Grained Access Control (FGAC), CloudTrail auditing, VPC Endpoints for private connectivity, and continuous monitoring through CloudWatch and AWS Config.

---

Another common question is:

> **How do you satisfy data retention requirements in DynamoDB?**

Use TTL for temporary data, Backup & Restore and PITR for recovery, Export to Amazon S3 for archival, and define retention policies that align with business and regulatory requirements.

---

# Key Takeaways

- Compliance is achieved through architecture, processes, and operational controls—not a single AWS feature.
- DynamoDB integrates with IAM, KMS, CloudTrail, CloudWatch, AWS Config, and Security Hub to support enterprise security requirements.
- Protect sensitive data using encryption, least privilege, auditing, and network isolation.
- Plan for data retention, archival, and secure deletion as part of the data lifecycle.
- Continuously monitor compliance and security posture using AWS-native observability and governance services.
- A well-designed DynamoDB security architecture can meet the requirements of many regulated industries while maintaining scalability and performance.