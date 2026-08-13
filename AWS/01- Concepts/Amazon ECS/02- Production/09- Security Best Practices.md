# ECS Security Best Practices

# Why Security Matters

Security failures are often more expensive than infrastructure failures.

A successful compromise can result in:

- Data Breaches
- Service Outages
- Financial Loss
- Compliance Violations
- Reputation Damage

Security should be designed into the architecture from the beginning.

---

# Security Philosophy

Modern cloud security follows:

```text
Assume Breach
```

instead of:

```text
Trust By Default
```

---

# Defense in Depth

Security should not rely on a single control.

Example:

```text
IAM
 ↓
Security Groups
 ↓
Private Subnets
 ↓
Encryption
 ↓
Monitoring
```

Multiple layers reduce risk.

---

# Zero Trust Model

Core principle:

```text
Never Trust
Always Verify
```

Every request should be validated.

---

# ECS Security Layers

Production ECS security includes:

```text
IAM
Networking
Encryption
Logging
Monitoring
Container Security
```

---

# IAM Hardening

IAM is the foundation of ECS security.

Most cloud security issues involve:

```text
Excessive Permissions
```

---

# Least Privilege

Grant only required permissions.

Good:

```text
s3:GetObject
```

---

Bad:

```text
AdministratorAccess
```

---

# Task Role Security

Applications should use:

```text
Task Roles
```

instead of static credentials.

---

Architecture

```text
Application
      ↓
Task Role
      ↓
AWS Service
```

---

Benefits

- Temporary credentials
- Reduced risk
- Easier auditing

---

# Task Execution Role Security

Execution role should only include:

```text
ECR Access
CloudWatch Access
Secrets Access
```

Avoid unnecessary permissions.

---

# Secrets Management

Never store:

```text
Passwords
API Keys
Tokens
```

inside:

- Source Code
- Docker Images
- Git Repositories

---

# Bad Example

```python
DB_PASSWORD = "password123"
```

---

# Good Example

```text
Secrets Manager
```

stores the secret securely.

---

# AWS Secrets Manager

Used for:

- Database Credentials
- API Tokens
- Third-Party Secrets

---

Benefits

```text
Encryption
Rotation
Auditability
```

---

# Parameter Store

Useful for:

```text
Configuration
Feature Flags
Environment Values
```

---

# KMS Encryption

AWS Key Management Service protects:

```text
Secrets
Storage
Logs
Databases
```

---

# Encryption Types

## At Rest

Data stored securely.

---

## In Transit

Data encrypted during transmission.

---

# Example

```text
Client
 ↓ HTTPS
ALB
 ↓ TLS
ECS
```

---

# Network Security

Networking is a critical security boundary.

Use:

```text
Private Subnets
Security Groups
```

---

# Public vs Private Architecture

Recommended:

```text
Internet
 ↓
ALB
 ↓
Private ECS Tasks
 ↓
Private Database
```

---

Avoid:

```text
Internet
 ↓
Public ECS Tasks
```

when possible.

---

# Security Groups

Think of Security Groups as:

```text
Stateful Firewalls
```

---

# Example Design

ALB Security Group

```text
Allow:
80
443
```

---

Task Security Group

```text
Allow:
8000
Only From ALB
```

---

Database Security Group

```text
Allow:
5432
Only From ECS
```

---

# Principle

```text
Deny By Default
```

Only allow required traffic.

---

# Network Segmentation

Separate:

```text
Public Tier
Application Tier
Data Tier
```

---

Architecture

```text
ALB
 ↓
ECS
 ↓
RDS
```

Each layer isolated.

---

# Image Security

Containers inherit vulnerabilities from images.

---

# Best Practice

Use:

```text
Official Images
Minimal Images
```

Examples:

```text
python:slim
alpine
distroless
```

---

# Avoid

```text
Unknown Public Images
```

without verification.

---

# Image Scanning

Scan images before deployment.

Tools:

```text
ECR Scanning
Trivy
Snyk
```

---

# Common Vulnerabilities

Examples:

- Outdated Packages
- Known CVEs
- Exposed Secrets

---

# CI/CD Security

Pipeline should include:

```text
Testing
Scanning
Validation
```

before deployment.

---

# OIDC Authentication

Preferred over:

```text
Access Keys
```

for GitHub Actions.

---

Benefits

- Short-lived credentials
- Reduced secret exposure

---

# Runtime Security

Security does not end after deployment.

Monitor:

```text
Container Activity
Network Activity
IAM Usage
```

---

# Runtime Risks

Examples:

```text
Unexpected Processes
Unauthorized Access
Crypto Mining
```

---

# CloudTrail

Records AWS API activity.

Provides:

```text
Who
What
When
```

for AWS actions.

---

# Example Events

```text
Delete Service
Modify Task Definition
Update IAM Policy
```

---

# Why CloudTrail Matters

Useful for:

- Auditing
- Compliance
- Incident Investigation

---

# GuardDuty

AWS threat detection service.

Monitors:

```text
IAM Activity
Network Activity
Threat Intelligence
```

---

# Example Detection

```text
Compromised Credentials
```

or

```text
Suspicious API Calls
```

---

# Security Monitoring

Monitor:

```text
Failed Logins
Permission Changes
Task Failures
Unexpected Traffic
```

---

# Security Incident Response

Typical workflow:

```text
Detection
 ↓
Investigation
 ↓
Containment
 ↓
Recovery
 ↓
Lessons Learned
```

---

# Example Incident

Compromised Container

Actions:

```text
Stop Task
Rotate Credentials
Review Logs
Patch Vulnerability
```

---

# Compliance Considerations

Common frameworks:

```text
SOC2
ISO 27001
HIPAA
PCI DSS
```

---

# ECS Compliance Practices

Examples:

```text
Encryption
Logging
Access Control
Auditing
```

---

# Production Security Architecture

```text
Internet
 ↓
WAF
 ↓
ALB
 ↓
Private ECS Tasks
 ↓
RDS
```

Supporting services:

```text
Secrets Manager
CloudTrail
GuardDuty
KMS
CloudWatch
```

---

# Security Checklist

## Identity

- Least privilege
- Task roles
- MFA for administrators

---

## Network

- Private subnets
- Restricted security groups
- Segmentation

---

## Data

- Encryption at rest
- Encryption in transit
- Secret management

---

## Monitoring

- CloudTrail
- GuardDuty
- Alarms

---

# Common Security Mistakes

## AdministratorAccess Everywhere

Risk:

Excessive permissions.

---

## Hardcoded Secrets

Risk:

Credential leakage.

---

## Public Databases

Risk:

External exposure.

---

## Unpatched Images

Risk:

Known vulnerabilities.

---

## Missing Audit Logs

Risk:

Poor incident investigation.

---

# Troubleshooting Security Issues

## Access Denied

Check:

```text
IAM Policy
Task Role
Resource Policy
```

---

## Secret Retrieval Failure

Check:

```text
Execution Role
Secrets Manager Permissions
```

---

## Unexpected Network Access

Check:

```text
Security Groups
NACLs
Route Tables
```

---

# Common Interview Questions

## What is Defense in Depth?

Multiple security layers protecting the system.

---

## Why Use Task Roles?

Avoid static credentials.

---

## Why Use Secrets Manager?

Secure secret storage and rotation.

---

## What is Zero Trust?

Never trust; always verify.

---

## Why Use Private Subnets?

Reduce attack surface.

---

## What Does GuardDuty Do?

Threat detection and monitoring.

---

# Senior Engineer Perspective

Security is not a feature.

It is a system-wide design principle.

The strongest ECS architectures combine:

```text
IAM
Networking
Encryption
Monitoring
Automation
```

into a layered defense model.

Senior engineers assume systems will be attacked and design controls to limit blast radius, detect compromise quickly, and recover safely.

---

# Key Takeaways

- Defense in Depth is essential.
- IAM should follow least privilege.
- Task Roles are preferred over static credentials.
- Secrets belong in Secrets Manager.
- Encryption should be enabled everywhere.
- Private subnet architectures improve security.
- CloudTrail and GuardDuty strengthen visibility.
- Security must be integrated throughout the ECS lifecycle.
