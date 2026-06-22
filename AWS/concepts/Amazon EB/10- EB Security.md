# 10- Elastic Beanstalk Security

---

# Introduction

Security is one of the most critical aspects of running production workloads on AWS.

A perfectly designed application can still be compromised if security is neglected.

Common security incidents include:

```text
Exposed Credentials
Public Databases
Open Security Groups
Misconfigured IAM Roles
Unencrypted Traffic
```

Elastic Beanstalk simplifies deployment, but security remains the responsibility of engineers.

Understanding security in Elastic Beanstalk requires understanding multiple AWS services working together.

---

# Shared Responsibility Model

One of the most important AWS concepts is the Shared Responsibility Model.

AWS is responsible for:

```text
Physical Security
Data Centers
Networking Infrastructure
Hardware
Virtualization Layer
```

Customers are responsible for:

```text
Applications
Data
IAM Permissions
Operating System Configuration
Network Security
Encryption
```

Elastic Beanstalk does not remove this responsibility.

---

# Security Architecture

A typical secure Elastic Beanstalk architecture looks like:

```text
Internet
    ↓
AWS WAF
    ↓
Application Load Balancer
    ↓
Elastic Beanstalk
    ↓
Private EC2 Instances
    ↓
RDS
```

Each layer provides protection.

---

# Security Layers

Production security should follow a layered approach.

```text
Network Security
IAM Security
Application Security
Data Security
Monitoring Security
```

This is known as:

```text
Defense In Depth
```

---

# Identity and Access Management (IAM)

IAM controls:

```text
Who
Can Access
What Resources
```

It is one of the most important security services in AWS.

---

# IAM Components

```text
Users
Groups
Roles
Policies
```

---

# IAM Roles in Elastic Beanstalk

Elastic Beanstalk relies heavily on IAM roles.

Common roles:

```text
Service Role
EC2 Instance Profile
Application Role
```

---

# Service Role

Allows Elastic Beanstalk to manage AWS resources.

Examples:

```text
Create Load Balancers
Create Auto Scaling Groups
Manage CloudWatch
```

Without proper permissions:

```text
Environment Creation Fails
```

---

# EC2 Instance Profile

Attached to EC2 instances.

Provides access to:

```text
S3
CloudWatch
Secrets Manager
Parameter Store
```

---

# Why Roles Are Better Than Credentials

Bad:

```python
AWS_ACCESS_KEY=ABC123
AWS_SECRET_KEY=XYZ456
```

Good:

```text
IAM Role
```

Benefits:

```text
No Hardcoded Credentials
Automatic Rotation
Improved Security
```

---

# Principle of Least Privilege

One of the most important security principles.

Grant only the permissions required.

Bad:

```text
AdministratorAccess
```

Good:

```text
Read Specific S3 Bucket
```

---

# Example

Instead of:

```text
S3 Full Access
```

Use:

```text
Read Bucket A
Write Bucket B
```

Only.

---

# Network Security

Network security determines:

```text
Who Can Reach Your Resources
```

Primary tools:

```text
VPC
Subnets
Security Groups
NACLs
```

---

# Virtual Private Cloud (VPC)

Elastic Beanstalk environments run inside a VPC.

Think of a VPC as:

```text
Private Network In AWS
```

---

# Typical Production Architecture

```text
Public Subnet
      ↓
ALB

Private Subnet
      ↓
EC2
      ↓
RDS
```

---

# Why Private Subnets Matter

Benefits:

```text
Reduced Attack Surface
Improved Security
Restricted Access
```

Production EC2 instances should usually not have public IP addresses.

---

# Security Groups

Security Groups act as virtual firewalls.

---

# Inbound Rules

Control:

```text
Incoming Traffic
```

Example:

```text
HTTPS
Port 443
```

---

# Outbound Rules

Control:

```text
Outgoing Traffic
```

Example:

```text
Database Connections
External APIs
```

---

# ALB Security Group

Example:

```text
Inbound:
443

Source:
Internet
```

---

# EC2 Security Group

Example:

```text
Inbound:
Application Port

Source:
ALB Security Group
```

Not:

```text
0.0.0.0/0
```

---

# Database Security Group

Example:

```text
Port:
5432

Source:
Elastic Beanstalk Security Group
```

Only.

---

# Common Security Group Mistake

Bad:

```text
Port 22
Source:
0.0.0.0/0
```

This exposes SSH to the internet.

---

# Secure Alternative

```text
Port 22
Source:
Corporate IP Range
```

or

```text
AWS Systems Manager
```

---

# HTTPS Security

Production systems should always use:

```text
HTTPS
```

---

# Why HTTPS Matters

Without HTTPS:

```text
User
 ↓
Plain Text Traffic
 ↓
Internet
```

Data can be intercepted.

---

# HTTPS Architecture

```text
User
 ↓
HTTPS
 ↓
ALB
 ↓
Application
```

---

# SSL Certificates

Elastic Beanstalk commonly uses:

```text
AWS Certificate Manager (ACM)
```

Benefits:

```text
Free
Managed
Automatic Renewal
```

---

# Encryption at Rest

Sensitive data should be encrypted while stored.

Examples:

```text
RDS
EBS
S3
EFS
```

---

# Encryption Architecture

```text
Application
      ↓
Encrypted Storage
```

---

# S3 Encryption

Recommended:

```text
SSE-S3
SSE-KMS
```

---

# RDS Encryption

Benefits:

```text
Data Protection
Compliance
Security
```

Enable encryption during database creation whenever possible.

---

# Encryption in Transit

Data should also be encrypted while moving.

Examples:

```text
HTTPS
TLS
SSL
```

---

# Secrets Management

One of the biggest beginner mistakes:

```python
SECRET_KEY = "mysecret"
```

or

```python
DB_PASSWORD = "password123"
```

---

# Why Hardcoded Secrets Are Dangerous

Risks:

```text
GitHub Exposure
Credential Theft
Security Breaches
```

---

# AWS Secrets Manager

Recommended solution.

Stores:

```text
Passwords
API Keys
Tokens
Certificates
```

Securely.

---

# Example Workflow

```text
Application
      ↓
Secrets Manager
      ↓
Retrieve Secret
```

---

# Systems Manager Parameter Store

Alternative to Secrets Manager.

Stores:

```text
Configuration Values
Environment Settings
Secrets
```

---

# Choosing Between Them

Parameter Store:

```text
Simple Configuration
```

Secrets Manager:

```text
Automatic Rotation
Advanced Secret Management
```

---

# Environment Variables

Applications often require:

```text
DATABASE_URL
SECRET_KEY
API_KEY
```

Use environment variables instead of hardcoded values.

---

# Logging and Auditing

Security requires visibility.

---

# CloudWatch Logs

Provides:

```text
Application Logs
System Logs
Deployment Logs
```

---

# AWS CloudTrail

Records:

```text
Who Did What
When
```

Examples:

```text
Deleted Environment
Modified Security Group
Created IAM Role
```

---

# Why CloudTrail Matters

Useful for:

```text
Auditing
Compliance
Incident Investigation
```

---

# Web Application Firewall (WAF)

AWS WAF protects applications against:

```text
SQL Injection
Cross-Site Scripting
Bot Attacks
Common Exploits
```

---

# Architecture

```text
Internet
 ↓
AWS WAF
 ↓
ALB
 ↓
Application
```

---

# DDoS Protection

AWS provides:

```text
AWS Shield Standard
```

automatically.

For advanced protection:

```text
AWS Shield Advanced
```

---

# Security Monitoring

Security is not a one-time activity.

Continuous monitoring is required.

---

# Common Monitoring Areas

```text
Unauthorized Access
Failed Logins
Permission Changes
Network Changes
```

---

# Amazon GuardDuty

Provides:

```text
Threat Detection
Anomaly Detection
Security Findings
```

---

# Security Compliance

Organizations may need compliance frameworks:

```text
SOC2
HIPAA
PCI-DSS
ISO 27001
```

Security controls help meet these requirements.

---

# Common Security Mistakes

---

## Public Database

Bad:

```text
Internet
 ↓
RDS
```

---

## Hardcoded Secrets

Bad:

```python
SECRET_KEY = "secret"
```

---

## Administrator Permissions

Bad:

```text
AdministratorAccess
```

for every user.

---

## Public EC2 Instances

Bad:

```text
Public EC2
Public Database
```

---

## No HTTPS

Bad:

```text
HTTP Only
```

---

## No Logging

Bad:

```text
No CloudTrail
No Monitoring
```

---

# Production Security Checklist

```text
HTTPS Enabled
Private Subnets
Least Privilege IAM
Encrypted Storage
Secrets Manager
CloudTrail Enabled
CloudWatch Monitoring
WAF Enabled
Regular Patching
Security Reviews
```

---

# Security Incident Example

Example:

```text
API Key Committed To GitHub
```

Response:

```text
Rotate Credential
Update Secret
Audit Access
Deploy Fix
```

This is why secrets should never be stored in code.

---

# Interview Questions

## What IAM Role Does Elastic Beanstalk Use?

Service Roles and Instance Profiles.

---

## What Is Least Privilege?

Grant only the permissions required.

---

## Why Use IAM Roles Instead of Access Keys?

Improved security and automatic credential management.

---

## What Is AWS WAF?

A Web Application Firewall protecting against common web attacks.

---

## How Should Secrets Be Stored?

```text
AWS Secrets Manager
```

or

```text
Parameter Store
```

---

## Why Use Private Subnets?

To reduce exposure to the public internet.

---

## Why Enable CloudTrail?

For auditing and security investigations.

---

## Should Production Use HTTPS?

```text
Always
```

---

# Senior Engineer Perspective

Security is not a feature.

Security is an architectural requirement.

A mature Elastic Beanstalk environment follows:

```text
Least Privilege
Encryption Everywhere
Private Networking
Continuous Monitoring
Automated Auditing
```

The goal is not simply preventing attacks.

The goal is:

```text
Reduce Risk
Limit Impact
Improve Recovery
```

because no system is completely immune to compromise.

---

# Key Takeaways

* Elastic Beanstalk security relies heavily on IAM, networking, encryption, and monitoring.
* Use IAM roles instead of access keys.
* Follow the Principle of Least Privilege.
* Deploy EC2 instances in private subnets whenever possible.
* Use HTTPS and ACM certificates.
* Store secrets in Secrets Manager or Parameter Store.
* Enable CloudTrail and CloudWatch.
* Consider AWS WAF and Shield for additional protection.
* Security should be integrated into architecture from day one.
