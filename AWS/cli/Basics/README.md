# AWS CLI Basics

> A comprehensive, production-focused guide to mastering the AWS Command Line Interface (AWS CLI) for Backend Engineers, DevOps Engineers, Cloud Engineers, and AWS Solutions Architects.

---

# Overview

The **AWS Command Line Interface (AWS CLI)** is one of the most important tools in the AWS ecosystem.

While the AWS Management Console is excellent for learning and exploration, experienced engineers rely heavily on the CLI for:

- Infrastructure automation
- Production deployments
- CI/CD pipelines
- Cloud operations
- Incident response
- Resource management
- Troubleshooting
- Infrastructure as Code (IaC)

This folder provides a structured, real-world guide to mastering AWS CLI—from installation and authentication to production automation and operational best practices.

Unlike traditional documentation, this guide focuses on **how experienced engineers actually use the AWS CLI in production**.

---

# Learning Objectives

After completing this section, you will be able to:

- Install and configure AWS CLI Version 2
- Understand AWS authentication and authorization
- Work with Named Profiles and IAM Roles
- Master global CLI options
- Filter output using JMESPath
- Build automation scripts
- Debug AWS CLI issues
- Follow production security best practices
- Prepare for AWS and Backend Engineering interviews

---

## Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Installation & Configuration](./01-%20Installation%20%26%20Configuration.md) | Install and configure AWS CLI |
| [02 - Authentication & Credentials](./02-%20Authentication%20%26%20Credentials.md) | IAM, Roles, Profiles, SSO |
| [03 - Global Options & Output Formats](./03-%20Global%20Options%20%26%20Output%20Formats.md) | `--profile`, `--region`, `--query`, `--output` |
| [04 - CLI Productivity & Automation](./04-%20CLI%20Productivity%20%26%20Automation.md) | Shell scripting, automation, workflows |
| [05 - Security & Troubleshooting](./05-%20Security%20%26%20Troubleshooting.md) | Security, debugging, production practices |
| [06 - Cheat Sheet & Interview Guide](./06-%20Cheat%20Sheet%20%26%20Interview%20Questions.md) | Quick reference, interview Q&A, runbooks |


---

# Reading Order

## 01. Installation & Configuration

Learn how to:

- Install AWS CLI Version 2
- Configure credentials
- Configure Regions
- Verify installation
- Understand configuration files

Recommended for anyone new to AWS CLI.

---

## 02. Authentication & Credentials

Covers:

- Authentication vs Authorization
- IAM Users
- IAM Roles
- Temporary Credentials
- Named Profiles
- Credential Provider Chain
- Environment Variables
- AWS IAM Identity Center (SSO)

One of the most important chapters in this guide.

---

## 03. Global Options & Output Formats

Learn how to use:

- `--profile`
- `--region`
- `--query`
- `--output`
- `--debug`
- `--cli-auto-prompt`

You'll also learn JMESPath filtering and output formatting.

---

## 04. CLI Productivity & Automation

Focuses on:

- Shell scripting
- Pipes and redirection
- Command skeletons
- Automation
- Variables
- Logging
- Production workflows

Ideal for engineers building deployment scripts and automation.

---

## 05. Security & Troubleshooting

Covers:

- Secure credential management
- Least Privilege
- Production best practices
- Common AWS CLI errors
- Troubleshooting workflows
- Operational checklists

A must-read before using AWS CLI in production.

---

## 06. Cheat Sheet & Interview Guide

Includes:

- Frequently used commands
- Interview questions
- Production runbooks
- Daily operational workflows
- Senior engineer recommendations

Designed as a quick-reference guide for daily work.

---

# Skills You'll Gain

By completing this folder, you'll learn how to:

- Configure AWS CLI securely
- Work with multiple AWS accounts
- Authenticate using IAM Roles and SSO
- Query AWS APIs efficiently
- Build reusable automation
- Troubleshoot production issues
- Secure AWS credentials
- Use AWS CLI effectively in CI/CD pipelines

---

# Prerequisites

Before starting, you should have:

- Basic AWS knowledge
- An AWS account (Free Tier is sufficient)
- AWS CLI Version 2 installed
- Basic Linux, macOS, or Windows terminal knowledge

No prior AWS CLI experience is required.

---

# Best Practices

Throughout this guide, we consistently follow these engineering principles:

- Prefer IAM Roles over IAM Users
- Use temporary credentials whenever possible
- Never use the Root account for daily operations
- Verify your identity before making production changes
- Specify Regions explicitly
- Follow the Principle of Least Privilege
- Automate repetitive tasks
- Log operational activities
- Validate before deploying

These practices reflect real-world engineering workflows.

---

# Recommended Learning Path

```
Installation
        │
        ▼
Authentication
        │
        ▼
Global Options
        │
        ▼
Automation
        │
        ▼
Security
        │
        ▼
Cheat Sheet
        │
        ▼
Service-Specific AWS CLI Commands
```

Following this order builds a strong conceptual foundation before moving on to AWS service-specific commands.


---

# Who Should Read This?

This guide is designed for:

- Backend Engineers
- Python Developers
- DevOps Engineers
- Platform Engineers
- Cloud Engineers
- Site Reliability Engineers (SREs)
- AWS Solutions Architects
- Students preparing for AWS interviews

---

# Key Takeaway

Mastering the AWS CLI is one of the highest-leverage skills for cloud engineers. It enables automation, improves operational efficiency, and forms the foundation for Infrastructure as Code, CI/CD pipelines, and day-to-day cloud operations.

This folder is intended to provide not just command references, but a production-ready understanding of how experienced engineers use the AWS CLI in real-world environments.


---

## Navigation

**🏠 Home**

- [AWS Playbook](../../README.md)

**📂 AWS CLI**

- [AWS CLI](../README.md)

---