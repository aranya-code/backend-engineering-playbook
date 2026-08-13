# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon ECR CLI commands, image management workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used ECR CLI commands
- Manage repositories and images
- Configure authentication
- Manage image scanning
- Configure lifecycle policies
- Integrate ECR into CI/CD pipelines
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon ECR is central to container platforms.

Instead of remembering every command, experienced engineers remember:

- Repository management
- Authentication
- Image lifecycle
- Security
- CI/CD workflow
- Deployment process

This chapter provides a quick operational reference.

---

# CLI Namespace

General syntax:

```bash
aws ecr <operation>
```

Examples:

```bash
aws ecr describe-repositories
```

```bash
aws ecr create-repository
```

```bash
aws ecr list-images
```

---

# Repository Commands

## List Repositories

```bash
aws ecr describe-repositories
```

---

## Create Repository

```bash
aws ecr create-repository
```

---

## Describe Repository

```bash
aws ecr describe-repositories \
--repository-names backend-api
```

---

## Delete Repository

```bash
aws ecr delete-repository
```

---

# Authentication Commands

## Authenticate Docker

```bash
aws ecr get-login-password \
| docker login \
--username AWS \
--password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
```

---

## Verify AWS Identity

```bash
aws sts get-caller-identity
```

---

# Image Commands

## List Images

```bash
aws ecr list-images
```

---

## Describe Images

```bash
aws ecr describe-images
```

---

## Delete Image

```bash
aws ecr batch-delete-image
```

---

## Start Image Scan

```bash
aws ecr start-image-scan
```

---

## View Scan Findings

```bash
aws ecr describe-image-scan-findings
```

---

# Lifecycle Policy Commands

## Apply Lifecycle Policy

```bash
aws ecr put-lifecycle-policy
```

---

## View Lifecycle Policy

```bash
aws ecr get-lifecycle-policy
```

---

## Preview Lifecycle Policy

```bash
aws ecr get-lifecycle-policy-preview
```

---

# Repository Policy Commands

## View Repository Policy

```bash
aws ecr get-repository-policy
```

---

## Apply Repository Policy

```bash
aws ecr set-repository-policy
```

---

# Registry Commands

## View Registry Configuration

```bash
aws ecr describe-registry
```

---

## Configure Replication

```bash
aws ecr put-replication-configuration
```

---

# Docker Commands

## Build Image

```bash
docker build -t backend-api .
```

---

## Tag Image

```bash
docker tag backend-api:latest \
ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/backend-api:v1.0.0
```

---

## Push Image

```bash
docker push \
ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/backend-api:v1.0.0
```

---

## Pull Image

```bash
docker pull \
ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/backend-api:v1.0.0
```

---

## List Local Images

```bash
docker images
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use named AWS profile |
| `--region` | Override Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable CLI debugging |
| `--no-cli-pager` | Disable pager |

---

# Amazon ECR Components

| Component | Purpose |
|-----------|----------|
| Registry | Top-level container registry |
| Repository | Stores related images |
| Image | Docker image |
| Tag | Human-readable version |
| Digest | Immutable image identifier |
| Lifecycle Policy | Automatic cleanup |
| Repository Policy | Access control |

---

# Common Image Tags

| Tag | Recommended |
|------|-------------|
| latest | ❌ Avoid in production |
| v1.0.0 | ✅ Recommended |
| v2.1.3 | ✅ Recommended |
| 2026-07-12 | ✅ Acceptable |

---

# Image Scan Severity

| Severity | Action |
|----------|--------|
| Critical | Fix immediately |
| High | Fix before production |
| Medium | Review |
| Low | Monitor |
| Informational | Optional |

---

# Common IAM Permissions

| Permission | Purpose |
|------------|---------|
| ecr:GetAuthorizationToken | Docker authentication |
| ecr:DescribeRepositories | View repositories |
| ecr:BatchGetImage | Pull images |
| ecr:GetDownloadUrlForLayer | Download image layers |
| ecr:PutImage | Push images |
| ecr:BatchDeleteImage | Delete images |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| RepositoryNotFoundException | Repository missing | Verify repository name |
| ImageNotFoundException | Image missing | Verify tag or digest |
| AccessDeniedException | IAM issue | Review IAM and repository policy |
| CannotPullContainerError | ECS image pull failed | Verify Task Execution Role |
| No Basic Auth Credentials | Docker not authenticated | Run `get-login-password` |
| ImageAlreadyExistsException | Immutable tag exists | Push a new version |
| ScanNotFoundException | Scan unavailable | Enable scanning and retry |

---

# Docker → ECR Workflow

```text
Docker Build

↓

Docker Tag

↓

Docker Login

↓

Docker Push

↓

Amazon ECR
```

---

# ECR → ECS Workflow

```text
Amazon ECR

↓

Task Definition

↓

Amazon ECS

↓

Container Starts
```

---

# CI/CD Workflow

```text
GitHub

↓

CodeBuild

↓

Docker Build

↓

Amazon ECR

↓

Amazon ECS
```

---

# Production Deployment Workflow

```text
Developer

↓

Git Push

↓

CI/CD

↓

Docker Build

↓

Image Scan

↓

Amazon ECR

↓

Amazon ECS

↓

Production
```

---

# Security Checklist

Every production repository should have:

- □ Private repository
- □ Immutable tags
- □ Scan on push enabled
- □ Lifecycle policy configured
- □ Least-privilege IAM policies
- □ Repository policy reviewed
- □ Encryption enabled
- □ Cross-region replication (if required)

---

# Repository Organization

Recommended structure:

```text
Repositories

│

├── backend-api

├── authentication

├── payments

├── inventory

├── orders

└── frontend
```

---

# Versioning Strategy

Recommended:

```text
v1.0.0

↓

v1.1.0

↓

v1.2.0

↓

v2.0.0
```

Avoid:

```text
latest
```

for production deployments.

---

# Troubleshooting Workflow

```text
Docker

↓

Authentication

↓

Amazon ECR

↓

Repository

↓

Image

↓

Amazon ECS
```

---

# Production Architecture

```text
Developer
      │
      ▼
GitHub
      │
      ▼
CI/CD Pipeline
      │
      ▼
Docker Build
      │
      ▼
Amazon ECR
      │
      ▼
Amazon ECS
      │
      ▼
Application Load Balancer
      │
      ▼
Users
```

---

# Interview Questions

## 1. What is Amazon ECR?

**Answer**

Amazon Elastic Container Registry (Amazon ECR) is AWS's fully managed container registry used to securely store, manage, scan, replicate, and distribute Docker container images.

---

## 2. What is the difference between an ECR Registry and a Repository?

**Answer**

A Registry is the top-level container registry associated with an AWS account and Region. A Repository is a logical collection of related container images stored within that registry.

---

## 3. Why should immutable image tags be used?

**Answer**

Immutable tags cannot be overwritten, ensuring deployments are reproducible, simplifying rollbacks, and preventing accidental replacement of production images.

---

## 4. What is image scanning?

**Answer**

Amazon ECR scans container images for known software vulnerabilities and reports findings categorized by severity levels such as Critical, High, Medium, and Low.

---

## 5. What are Lifecycle Policies?

**Answer**

Lifecycle Policies automatically delete old or untagged images based on configurable rules, helping reduce storage costs and keep repositories organized.

---

## 6. How does Amazon ECS authenticate with Amazon ECR?

**Answer**

Amazon ECS uses the **Task Execution Role** to request an authorization token from Amazon ECR. The ECS agent then downloads the required image layers before starting the container.

---

## 7. What is the purpose of Repository Policies?

**Answer**

Repository Policies provide resource-based access control, allowing you to grant or restrict image access to IAM users, roles, AWS accounts, or AWS services, including enabling secure cross-account image sharing.

---

## 8. Why should `latest` not be used in production?

**Answer**

The `latest` tag is mutable and may reference different image versions over time. Immutable version tags or image digests ensure predictable deployments and simplify troubleshooting and rollbacks.

---

## 9. How does Amazon ECR integrate into a CI/CD pipeline?

**Answer**

A CI/CD pipeline builds a Docker image, authenticates with Amazon ECR, pushes the image to a repository, optionally scans it for vulnerabilities, and then updates an ECS Service or Lambda function to deploy the new image.

---

## 10. How would you troubleshoot a `CannotPullContainerError` in ECS?

**Answer**

I would verify the image exists in Amazon ECR, confirm the repository URI and image tag, check that the ECS Task Execution Role has the required ECR permissions, validate repository policies, and review ECS task events and CloudWatch Logs for authentication or networking failures.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Build images only in CI/CD pipelines.
- Use immutable version tags or image digests.
- Enable **scan on push** for all repositories.
- Configure lifecycle policies to remove stale images.
- Separate repositories by application or microservice.
- Restrict image push access to automation systems.
- Use private repositories for production workloads.
- Enable cross-Region replication for disaster recovery.
- Store Dockerfiles in version control.
- Monitor repository growth and vulnerability reports regularly.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Repositories | `aws ecr describe-repositories` |
| Create Repository | `aws ecr create-repository` |
| Authenticate Docker | `aws ecr get-login-password` |
| List Images | `aws ecr list-images` |
| Describe Images | `aws ecr describe-images` |
| Delete Image | `aws ecr batch-delete-image` |
| Start Scan | `aws ecr start-image-scan` |
| View Scan Findings | `aws ecr describe-image-scan-findings` |
| Apply Lifecycle Policy | `aws ecr put-lifecycle-policy` |
| Configure Replication | `aws ecr put-replication-configuration` |

---

# Final Thoughts

Amazon ECR is the foundation of container image management in AWS. When combined with Docker, Amazon ECS, Amazon EKS, AWS Lambda, CodeBuild, CodePipeline, IAM, and Amazon Inspector, it provides a secure, scalable, and enterprise-ready platform for storing and distributing container images. Mastering the ECR CLI enables backend and cloud engineers to automate deployments, improve security, optimize storage, and build reliable CI/CD pipelines.

---
