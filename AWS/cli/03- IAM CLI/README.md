# AWS IAM CLI

> A comprehensive, production-focused guide to managing AWS Identity and Access Management (IAM) using the AWS Command Line Interface (AWS CLI). Learn user and role management, policy design, authentication, security best practices, IAM Identity Center (SSO), troubleshooting, and interview-focused concepts.

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to IAM CLI](./01-%20Introduction%20to%20IAM%20CLI.md) | Learn IAM fundamentals, authentication vs authorization, IAM resources, and AWS CLI command structure |
| [02 - IAM Users, Groups & Roles](./02-%20IAM%20Users,%20Groups%20%26%20Roles.md) | Create and manage IAM Users, Groups, Roles, Instance Profiles, and AssumeRole workflows |
| [03 - IAM Policies](./03-%20IAM%20Policies.md) | Learn policy structure, JSON syntax, policy evaluation, permission boundaries, and least privilege |
| [04 - Access Keys, MFA & Security](./04-%20Access%20Keys,%20MFA%20%26%20Security.md) | Manage Access Keys, MFA, password policies, credential reports, and IAM security best practices |
| [05 - IAM Identity Center (SSO)](./05-%20IAM%20Identity%20Center%20(SSO).md) | Configure AWS CLI with SSO, Permission Sets, AWS Organizations integration, and enterprise authentication |
| [06 - Troubleshooting & Best Practices](./06-%20Troubleshooting%20%26%20Best%20Practices.md) | Troubleshoot IAM permission issues, policy evaluation, authentication failures, and production security |
| [07 - Cheat Sheet & Interview Guide](./07-%20Cheat%20Sheet%20%26%20Interview%20Guide.md) | Frequently used IAM CLI commands, troubleshooting reference, interview questions, and operational workflows |

---

# Overview

AWS Identity and Access Management (IAM) is the security foundation of every AWS environment.

Every request to an AWS service is authenticated and authorized through IAM before access is granted.

Although IAM can be managed through the AWS Management Console, production environments rely heavily on the AWS CLI and Infrastructure as Code (IaC) for automation, identity management, security audits, and enterprise-scale administration.

This guide focuses on how Backend Engineers, DevOps Engineers, Cloud Engineers, and AWS Solutions Architects manage IAM in real-world production environments.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand AWS IAM architecture
- Create and manage IAM Users, Groups, and Roles
- Design secure IAM Policies
- Configure Access Keys and Multi-Factor Authentication (MFA)
- Use IAM Identity Center (SSO) with the AWS CLI
- Implement least-privilege access
- Troubleshoot IAM permission issues
- Secure AWS accounts following AWS best practices
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
AWS IAM CLI/
│
├── 01- Introduction to IAM CLI.md
├── 02- IAM Users, Groups & Roles.md
├── 03- IAM Policies.md
├── 04- Access Keys, MFA & Security.md
├── 05- IAM Identity Center (SSO).md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to IAM CLI

Build a strong IAM foundation by learning:

- Authentication vs Authorization
- IAM architecture
- IAM resources
- IAM CLI command structure
- Identity verification
- IAM evaluation flow

---

## 02. IAM Users, Groups & Roles

Learn how to:

- Create IAM Users
- Manage Groups
- Create IAM Roles
- Configure Trust Policies
- Use Instance Profiles
- Implement AssumeRole
- Manage cross-account access

---

## 03. IAM Policies

Master:

- AWS Managed Policies
- Customer Managed Policies
- Inline Policies
- JSON policy syntax
- Actions, Resources, Conditions
- Explicit vs Implicit Deny
- Permission Boundaries
- Policy evaluation logic

---

## 04. Access Keys, MFA & Security

Topics include:

- Access Keys
- Secret Access Keys
- Key rotation
- Password Policies
- Multi-Factor Authentication (MFA)
- Credential Reports
- IAM Access Analyzer
- Security audits

---

## 05. IAM Identity Center (SSO)

Learn:

- AWS IAM Identity Center
- AWS CLI SSO configuration
- Permission Sets
- Identity Providers
- AWS Organizations integration
- Enterprise authentication
- Temporary credentials

---

## 06. Troubleshooting & Best Practices

Master:

- AccessDenied troubleshooting
- IAM policy debugging
- STS troubleshooting
- AssumeRole issues
- Credential problems
- Security audits
- Production operational checklists

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used IAM CLI commands
- Policy management commands
- STS commands
- SSO commands
- Troubleshooting commands
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Secure AWS environments using IAM
- Build least-privilege permission models
- Manage enterprise identities
- Configure secure authentication
- Automate IAM administration
- Troubleshoot complex permission issues
- Implement production-grade IAM security

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Understand basic AWS concepts.
- Have AWS CLI Version 2 installed.
- Have access to an AWS account.
- Be familiar with AWS Profiles and Regions.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Prefer IAM Roles over IAM Users.
- Enable MFA for all privileged users.
- Follow the Principle of Least Privilege.
- Use Customer Managed Policies.
- Avoid wildcard (`*`) permissions whenever possible.
- Rotate Access Keys regularly.
- Use IAM Identity Center for workforce authentication.
- Review IAM policies and permissions periodically.
- Audit IAM using Credential Reports and Access Analyzer.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
Users, Groups & Roles
      │
      ▼
IAM Policies
      │
      ▼
Access Keys & MFA
      │
      ▼
IAM Identity Center
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this order builds a strong understanding of AWS identity management before moving into advanced security and enterprise authentication.

---

# Real-World Use Cases

The skills in this guide apply to:

- AWS account administration
- Enterprise identity management
- CI/CD authentication
- Cross-account access
- EC2 IAM Roles
- Lambda execution roles
- Kubernetes IAM integration
- Security audits
- Compliance
- Infrastructure automation

---

# What's Next?

After mastering AWS IAM CLI, continue with:

- CloudFormation CLI
- CloudWatch CLI
- Lambda CLI
- ECR CLI
- ECS CLI
- RDS CLI
- DynamoDB CLI
- SQS CLI
- SNS CLI
- Route 53 CLI
- VPC CLI

Each guide follows the same structure, making it easy to learn additional AWS services.

---

# Who Should Read This?

This guide is designed for:

- Backend Engineers
- DevOps Engineers
- Cloud Engineers
- Platform Engineers
- Site Reliability Engineers (SREs)
- AWS Solutions Architects
- Security Engineers
- Students preparing for AWS certifications
- Engineers preparing for backend and cloud interviews

---

# Learning Outcomes

By the end of this guide, you will be able to:

- ✅ Manage IAM Users, Groups, and Roles confidently.
- ✅ Design secure IAM Policies following least-privilege principles.
- ✅ Configure Access Keys, MFA, and account security.
- ✅ Use IAM Identity Center (SSO) with the AWS CLI.
- ✅ Troubleshoot IAM permission issues systematically.
- ✅ Audit IAM security using AWS-native tools.
- ✅ Implement production-ready identity and access management.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

AWS IAM is the security backbone of the AWS platform. Mastering the IAM CLI enables you to automate identity management, implement least-privilege access, secure applications with temporary credentials, and manage enterprise authentication at scale. Combined with IAM Roles, IAM Identity Center, and robust policy design, these skills form the foundation of secure, production-ready AWS environments.

---

## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **AWS IAM CLI** |

---