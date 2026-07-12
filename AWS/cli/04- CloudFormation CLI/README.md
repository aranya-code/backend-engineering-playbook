# AWS CloudFormation CLI

> A comprehensive, production-focused guide to provisioning and managing AWS infrastructure using AWS CloudFormation and the AWS Command Line Interface (AWS CLI). Learn Infrastructure as Code (IaC), stack management, Change Sets, StackSets, Nested Stacks, deployment strategies, troubleshooting, and production best practices.

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to CloudFormation CLI](./01-%20Introduction%20to%20CloudFormation%20CLI.md) | Learn Infrastructure as Code (IaC), CloudFormation architecture, stacks, templates, and CLI fundamentals |
| [02 - Stacks & Templates](./02-%20Stacks%20%26%20Templates.md) | Build CloudFormation templates using YAML, Parameters, Outputs, Resources, Conditions, and Intrinsic Functions |
| [03 - Stack Operations](./03-%20Stack%20Operations.md) | Create, update, delete, rollback, protect, import, and manage CloudFormation stacks |
| [04 - Change Sets, Drift Detection & StackSets](./04-%20Change%20Sets,%20Drift%20Detection%20%26%20StackSets.md) | Preview infrastructure changes, detect configuration drift, and deploy across multiple accounts and Regions |
| [05 - Nested Stacks, Parameters & Outputs](./05-%20Nested%20Stacks,%20Parameters%20%26%20Outputs.md) | Design modular templates using Nested Stacks, Cross-Stack References, Parameters, Outputs, and Intrinsic Functions |
| [06 - Troubleshooting & Best Practices](./06-%20Troubleshooting%20%26%20Best%20Practices.md) | Troubleshoot deployments, rollback failures, template issues, and follow production deployment practices |
| [07 - Cheat Sheet & Interview Guide](./07-%20Cheat%20Sheet%20%26%20Interview%20Guide.md) | Frequently used CloudFormation CLI commands, troubleshooting reference, interview questions, and operational workflows |

---

# Overview

AWS CloudFormation is AWS's native **Infrastructure as Code (IaC)** service.

Instead of manually provisioning infrastructure through the AWS Console, CloudFormation allows you to define your infrastructure in YAML or JSON templates and deploy it repeatedly, consistently, and automatically.

CloudFormation is one of the most widely used AWS services in modern DevOps, Platform Engineering, Cloud Engineering, and Backend Engineering because it enables infrastructure automation, version control, disaster recovery, and CI/CD integration.

This guide focuses on how experienced engineers use the **CloudFormation CLI** to manage production infrastructure.

---

# Learning Objectives

After completing this section, you will be able to:

- Understand Infrastructure as Code (IaC)
- Build reusable CloudFormation templates
- Deploy and manage CloudFormation stacks
- Work with Parameters, Outputs, and Intrinsic Functions
- Safely deploy infrastructure using Change Sets
- Detect and manage infrastructure drift
- Deploy infrastructure across multiple AWS accounts using StackSets
- Troubleshoot production deployments
- Prepare for AWS certification and backend engineering interviews

---

# Folder Structure

```text
AWS CloudFormation CLI/
│
├── 01- Introduction to CloudFormation CLI.md
├── 02- Stacks & Templates.md
├── 03- Stack Operations.md
├── 04- Change Sets, Drift Detection & StackSets.md
├── 05- Nested Stacks, Parameters & Outputs.md
├── 06- Troubleshooting & Best Practices.md
├── 07- Cheat Sheet & Interview Guide.md
└── README.md
```

---

# Reading Order

## 01. Introduction to CloudFormation CLI

Build a strong foundation by learning:

- Infrastructure as Code (IaC)
- CloudFormation architecture
- Templates
- Stacks
- Stack lifecycle
- CloudFormation CLI fundamentals

---

## 02. Stacks & Templates

Learn how to:

- Write YAML templates
- Understand template sections
- Use Parameters
- Configure Outputs
- Build reusable templates
- Validate templates
- Deploy infrastructure

---

## 03. Stack Operations

Master:

- Creating stacks
- Updating stacks
- Deleting stacks
- Rollback behavior
- Stack Policies
- Resource imports
- Stack lifecycle management

---

## 04. Change Sets, Drift Detection & StackSets

Topics include:

- Change Sets
- Safe infrastructure updates
- Resource replacement
- Drift Detection
- StackSets
- Multi-account deployments
- Multi-region deployments

---

## 05. Nested Stacks, Parameters & Outputs

Learn:

- Nested Stacks
- Cross-stack references
- Parameters
- Outputs
- Exports and Imports
- Intrinsic Functions
- Modular infrastructure design

---

## 06. Troubleshooting & Best Practices

Master:

- Deployment failures
- Rollback recovery
- Stack event analysis
- IAM permission issues
- Drift troubleshooting
- Production deployment strategies

---

## 07. Cheat Sheet & Interview Guide

A practical reference containing:

- Frequently used CloudFormation CLI commands
- Stack management commands
- Change Set commands
- Drift Detection commands
- StackSet commands
- Troubleshooting reference
- Interview questions
- Senior engineer recommendations

---

# Skills You'll Gain

After completing this folder, you'll be able to:

- Design Infrastructure as Code using CloudFormation
- Build reusable infrastructure templates
- Deploy infrastructure safely using Change Sets
- Manage production CloudFormation stacks
- Detect and resolve infrastructure drift
- Deploy infrastructure across multiple AWS accounts and Regions
- Troubleshoot CloudFormation deployments
- Integrate CloudFormation into CI/CD pipelines

---

# Prerequisites

Before starting this section, you should:

- Complete the **AWS CLI Basics** section.
- Understand AWS IAM fundamentals.
- Be familiar with EC2, S3, and networking basics.
- Have AWS CLI Version 2 installed.
- Have permissions to create CloudFormation stacks.

---

# Best Practices

Throughout this guide, we follow these production principles:

- Treat infrastructure as code.
- Store templates in Git.
- Prefer YAML over JSON.
- Validate templates before deployment.
- Use Parameters instead of hardcoded values.
- Review Change Sets before production deployments.
- Run Drift Detection regularly.
- Avoid manual changes to CloudFormation-managed resources.
- Use Nested Stacks for modular infrastructure.
- Automate deployments through CI/CD pipelines.

---

# Recommended Learning Path

```text
Introduction
      │
      ▼
Stacks & Templates
      │
      ▼
Stack Operations
      │
      ▼
Change Sets
      │
      ▼
Nested Stacks
      │
      ▼
Troubleshooting
      │
      ▼
Cheat Sheet & Interview Guide
```

Following this order builds a solid understanding of Infrastructure as Code before moving into enterprise deployment strategies.

---

# Real-World Use Cases

The skills in this guide apply to:

- Infrastructure as Code (IaC)
- Application deployment
- CI/CD automation
- Disaster recovery
- Environment provisioning
- Multi-account AWS environments
- Multi-region deployments
- Enterprise infrastructure management
- Compliance and governance
- Cloud automation

---

# What's Next?

After mastering AWS CloudFormation CLI, continue with:

- CloudWatch CLI
- Lambda CLI
- VPC CLI
- ECS CLI
- ECR CLI
- RDS CLI
- DynamoDB CLI
- SQS CLI
- SNS CLI
- Route 53 CLI
- API Gateway CLI

Each guide follows the same structure, allowing you to build consistent knowledge across AWS services.

---

# Who Should Read This?

This guide is designed for:

- Backend Engineers
- DevOps Engineers
- Cloud Engineers
- Platform Engineers
- Site Reliability Engineers (SREs)
- AWS Solutions Architects
- Infrastructure Engineers
- Students preparing for AWS certifications
- Engineers preparing for backend and cloud interviews

---

# Learning Outcomes

By the end of this guide, you will be able to:

- ✅ Design and deploy Infrastructure as Code using CloudFormation.
- ✅ Build reusable and modular CloudFormation templates.
- ✅ Manage CloudFormation stacks throughout their lifecycle.
- ✅ Safely update infrastructure using Change Sets.
- ✅ Detect and resolve infrastructure drift.
- ✅ Deploy infrastructure across multiple AWS accounts and Regions.
- ✅ Troubleshoot CloudFormation deployments in production.
- ✅ Prepare for AWS certification and backend engineering interviews.

---

# Key Takeaway

AWS CloudFormation is the foundation of Infrastructure as Code on AWS. Mastering the CloudFormation CLI enables you to provision, update, and manage cloud infrastructure in a repeatable, auditable, and automated manner. Combined with Git, CI/CD pipelines, Change Sets, StackSets, and modular template design, CloudFormation provides a scalable and reliable approach to managing production infrastructure across organizations of any size.

---

## Navigation

| Level | Link |
|-------|------|
| 🏠 Repository | [Backend Engineering Playbook](../../../README.md) |
| ☁️ AWS | [AWS](../../README.md) |
| 💻 AWS CLI | [CLI](../README.md) |
| 📖 Current Section | **AWS CloudFormation CLI** |

---