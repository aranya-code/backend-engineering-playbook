# ECS Terraform Deployment

# What is Infrastructure as Code?

Infrastructure as Code (IaC) means:

```text
Infrastructure
Defined As Code
```

instead of manually creating resources.

---

# Traditional Infrastructure

Example:

```text
AWS Console
 ↓
Click Resources
 ↓
Manual Configuration
```

Problems:

- Error-prone
- Hard to reproduce
- Difficult to review

---

# Infrastructure as Code

Example:

```text
Terraform Code
      ↓
Version Control
      ↓
Automated Deployment
```

Benefits:

- Repeatability
- Consistency
- Automation
- Auditing

---

# Why Terraform?

Terraform is an Infrastructure as Code tool.

It allows engineers to define:

```text
Networks
Compute
Storage
Security
```

using code.

---

# Terraform Workflow

```text
Write Code
     ↓
terraform plan
     ↓
terraform apply
     ↓
Infrastructure Created
```

---

# Terraform Core Concepts

Important concepts:

```text
Providers
Resources
Variables
Outputs
State
Modules
```

---

# Providers

Providers allow Terraform to communicate with platforms.

Example:

```hcl
provider "aws" {
  region = "ap-south-1"
}
```

---

# Resources

Resources represent infrastructure.

Example:

```hcl
resource "aws_ecs_cluster" "main" {
  name = "ecs-cluster"
}
```

---

# Variables

Variables improve reusability.

Example:

```hcl
variable "environment" {
  type = string
}
```

---

# Outputs

Expose useful values.

Example:

```hcl
output "cluster_name" {
  value = aws_ecs_cluster.main.name
}
```

---

# Terraform State

Terraform tracks infrastructure using:

```text
terraform.tfstate
```

---

Purpose:

```text
Current Infrastructure Snapshot
```

---

# Why State Matters

Terraform compares:

```text
Desired State
```

with

```text
Actual State
```

---

# Local State Problems

Example:

```text
Developer Laptop
```

---

Risks:

- Lost state
- Team conflicts
- No locking

---

# Remote State

Best Practice:

```text
S3
 +
DynamoDB Locking
```

---

Architecture

```text
Terraform
      ↓
S3 State
      ↓
DynamoDB Lock
```

---

# Terraform Project Structure

Example:

```text
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── terraform.tfvars
└── modules/
```

---

# Recommended Production Structure

```text
terraform/
├── environments/
│   ├── dev
│   ├── stage
│   └── prod
│
├── modules/
│   ├── vpc
│   ├── alb
│   ├── ecs
│   ├── rds
│   └── security
```

---

# VPC Module

Responsible for:

```text
VPC
Subnets
Route Tables
Internet Gateway
NAT Gateway
```

---

# Example VPC

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
```

---

# ECS Cluster Deployment

Example:

```hcl
resource "aws_ecs_cluster" "main" {
  name = "production-cluster"
}
```

---

# ECR Repository

Store Docker images.

Example:

```hcl
resource "aws_ecr_repository" "app" {
  name = "backend-app"
}
```

---

# Security Groups

Example:

```hcl
resource "aws_security_group" "ecs" {
  name = "ecs-sg"
}
```

---

# ALB Deployment

Example:

```hcl
resource "aws_lb" "app" {
  name               = "app-alb"
  load_balancer_type = "application"
}
```

---

# Target Groups

Example:

```hcl
resource "aws_lb_target_group" "app" {
  port     = 8000
  protocol = "HTTP"
}
```

---

# ECS Task Definition

Example:

```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "backend"
  requires_compatibilities = ["FARGATE"]
}
```

---

# ECS Service

Example:

```hcl
resource "aws_ecs_service" "app" {
  name            = "backend-service"
  desired_count   = 2
}
```

---

# IAM Roles

Terraform should manage:

```text
Task Role
Execution Role
```

---

Example

```hcl
resource "aws_iam_role" "ecs_task_role" {}
```

---

# Environment Separation

Never use:

```text
One Terraform Workspace
For Everything
```

---

Preferred:

```text
Dev
Stage
Prod
```

separated.

---

# Example Layout

```text
environments/
 ├── dev
 ├── stage
 └── prod
```

---

# Variables Example

```hcl
variable "desired_count" {
  default = 2
}
```

---

# Environment Overrides

Dev:

```text
desired_count = 1
```

---

Production:

```text
desired_count = 6
```

---

# Terraform Plan

Before applying:

```bash
terraform plan
```

---

Purpose:

Preview changes.

---

# Terraform Apply

Deploy infrastructure.

```bash
terraform apply
```

---

# Terraform Destroy

Remove resources.

```bash
terraform destroy
```

---

# CI/CD Integration

Pipeline:

```text
GitHub
 ↓
Terraform Plan
 ↓
Approval
 ↓
Terraform Apply
```

---

# GitHub Actions Example

```text
Push
 ↓
Plan
 ↓
Review
 ↓
Deploy
```

---

# Terraform Validation

Validate syntax.

```bash
terraform validate
```

---

# Terraform Formatting

Format files.

```bash
terraform fmt
```

---

# Terraform Best Practices

## Use Modules

Avoid duplication.

---

## Use Remote State

Enable collaboration.

---

## Review Plans

Never blindly apply.

---

## Tag Resources

Improve governance.

---

## Separate Environments

Reduce risk.

---

## Protect Production

Require approvals.

---

# Common Terraform Mistakes

## Hardcoded Values

Problem:

Poor reusability.

---

## Shared State Files

Problem:

State corruption.

---

## No Code Reviews

Problem:

Production risk.

---

## Manual Infrastructure Changes

Problem:

Terraform drift.

---

# Terraform Drift

Occurs when:

```text
AWS Console Changes
```

bypass Terraform.

---

Solution:

```text
Manage Infrastructure
Through Code
```

---

# Production ECS Architecture

Terraform Manages:

```text
VPC
ALB
Security Groups
ECR
ECS Cluster
Task Definitions
Services
CloudWatch
IAM
```

---

# Production Workflow

```text
Git Commit
      ↓
Terraform Plan
      ↓
Code Review
      ↓
Apply
      ↓
Infrastructure Updated
```

---

# Common Interview Questions

## What is Terraform State?

Infrastructure tracking mechanism.

---

## Why Use Remote State?

Collaboration and locking.

---

## Why Use Modules?

Reusable infrastructure.

---

## What is Terraform Drift?

Infrastructure changed outside Terraform.

---

## Why Use terraform plan?

Preview changes before deployment.

---

## Why Separate Environments?

Reduce deployment risk.

---

# Senior Engineer Perspective

Terraform is not simply a provisioning tool.

It is:

```text
Infrastructure Version Control
```

for cloud environments.

The goal is not just automation.

The goal is:

- Repeatability
- Reliability
- Auditability
- Scalability

Production teams should be able to rebuild infrastructure entirely from code.

---

# Key Takeaways

- Infrastructure should be managed as code.
- Terraform improves consistency and repeatability.
- Remote state is essential for teams.
- Modules improve maintainability.
- Separate environments reduce risk.
- CI/CD should automate infrastructure delivery.
- Terraform enables reproducible ECS deployments.
