# Introduction to CloudFormation CLI

> Learn how to provision and manage AWS infrastructure using AWS CloudFormation and the AWS Command Line Interface (AWS CLI). This chapter introduces Infrastructure as Code (IaC), CloudFormation concepts, stack architecture, and the most commonly used CloudFormation CLI commands.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Infrastructure as Code (IaC)
- Understand CloudFormation architecture
- Navigate CloudFormation CLI commands
- Understand Stacks and Templates
- List CloudFormation stacks
- Describe stack resources
- Build a foundation for Infrastructure as Code

---

# Why Learn CloudFormation CLI?

CloudFormation is AWS's Infrastructure as Code (IaC) service.

Instead of manually creating resources through the AWS Console, CloudFormation allows you to define infrastructure using templates.

Backend Engineers, DevOps Engineers, Platform Engineers, and Cloud Engineers use CloudFormation to:

- Provision infrastructure
- Standardize deployments
- Automate environments
- Version infrastructure
- Build CI/CD pipelines
- Recover environments
- Deploy multi-region architectures

The AWS CLI is commonly used to automate CloudFormation operations in production.

---

# What is Infrastructure as Code (IaC)?

Infrastructure as Code means infrastructure is defined using code rather than manual configuration.

Instead of:

```text
AWS Console

↓

Click

↓

Create EC2

↓

Create S3

↓

Create IAM Role
```

Use:

```text
CloudFormation Template

↓

CloudFormation

↓

Entire Infrastructure Created Automatically
```

Infrastructure becomes:

- Repeatable
- Version controlled
- Automated
- Consistent

---

# How AWS CLI Communicates with CloudFormation

CloudFormation commands follow this pattern:

```bash
aws cloudformation <operation>
```

Examples:

```bash
aws cloudformation list-stacks
```

```bash
aws cloudformation create-stack
```

```bash
aws cloudformation update-stack
```

```bash
aws cloudformation delete-stack
```

Every command maps directly to a CloudFormation API.

---

# Understanding CloudFormation Resources

CloudFormation manages AWS resources using templates.

```text
CloudFormation
│
├── Stacks
├── Templates
├── Parameters
├── Outputs
├── Resources
├── Change Sets
├── Nested Stacks
├── StackSets
└── Drift Detection
```

---

# Core CloudFormation Components

## Template

A YAML or JSON document describing infrastructure.

---

## Stack

A running deployment created from a template.

---

## Resource

An AWS service managed by CloudFormation.

Examples:

- EC2
- S3
- Lambda
- IAM
- DynamoDB

---

## Parameters

User-provided values supplied during deployment.

---

## Outputs

Values exported after deployment.

---

# CloudFormation Architecture

```text
Template
      │
      ▼
CloudFormation
      │
      ▼
Stack
      │
      ▼
AWS Resources
```

---

# List Existing Stacks

```bash
aws cloudformation list-stacks
```

Returns:

- Stack Name
- Stack Status
- Creation Time

---

# Describe a Stack

```bash
aws cloudformation describe-stacks \
--stack-name backend-production
```

Useful information includes:

- Parameters
- Outputs
- Stack Status
- Tags

---

# List Stack Resources

```bash
aws cloudformation list-stack-resources \
--stack-name backend-production
```

Returns every AWS resource managed by the stack.

---

# View Stack Events

```bash
aws cloudformation describe-stack-events \
--stack-name backend-production
```

Essential when troubleshooting failed deployments.

---

# Understanding Stack Lifecycle

```text
Create Stack
      │
      ▼
CREATE_IN_PROGRESS
      │
      ▼
CREATE_COMPLETE
      │
      ▼
Update Stack
      │
      ▼
UPDATE_COMPLETE
      │
      ▼
Delete Stack
      │
      ▼
DELETE_COMPLETE
```

---

# Viewing Stack Status

```bash
aws cloudformation describe-stacks \
--query "Stacks[].StackStatus"
```

Example:

```text
CREATE_COMPLETE
```

---

# Global CLI Options

Examples:

```bash
aws cloudformation list-stacks \
--profile production
```

```bash
aws cloudformation list-stacks \
--region ap-south-1
```

```bash
aws cloudformation list-stacks \
--output table
```

---

# Production Tip

Always verify your identity before creating or updating infrastructure.

```bash
aws sts get-caller-identity
```

Also verify the Region:

```bash
aws configure get region
```

Deploying infrastructure in the wrong account or Region is a common production mistake.

---

# Architecture Note

```text
Developer
      │
      ▼
AWS CLI
      │
      ▼
CloudFormation API
      │
      ▼
CloudFormation Stack
      │
      ▼
AWS Resources
```

CloudFormation orchestrates the creation, update, and deletion of AWS resources while maintaining dependency order.

---

# Interview Note

### Question

**What is the difference between CloudFormation and the AWS Management Console?**

### Answer

The AWS Management Console is used to manually create and manage resources through a graphical interface. CloudFormation defines infrastructure as code using templates, allowing environments to be deployed automatically, consistently, and repeatedly. CloudFormation is preferred for production environments because templates can be version controlled, reviewed, and integrated into CI/CD pipelines.

---

# Key Takeaways

- CloudFormation is AWS's Infrastructure as Code service.
- Infrastructure is defined using templates and deployed as stacks.
- CloudFormation CLI commands use the `aws cloudformation` namespace.
- Stacks manage collections of AWS resources.
- Always review stack events when troubleshooting deployments.
- Infrastructure as Code enables repeatable, automated, and auditable deployments.

---
