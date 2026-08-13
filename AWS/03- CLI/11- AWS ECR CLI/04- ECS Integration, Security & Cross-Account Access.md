# ECS Integration, Security & Cross-Account Access

> Learn how Amazon ECR integrates with Amazon ECS, AWS Lambda, IAM, AWS CodeBuild, and CI/CD pipelines. This chapter also covers repository security, IAM permissions, repository policies, cross-account access, image signing concepts, encryption, and production security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Integrate Amazon ECR with ECS
- Secure repositories using IAM
- Configure Repository Policies
- Enable cross-account image access
- Understand ECR encryption
- Build secure CI/CD workflows
- Apply production security best practices

---

# Amazon ECR Integrations

Amazon ECR integrates with many AWS services.

```text
Amazon ECR

│

├── Amazon ECS

├── Amazon EKS

├── AWS Lambda

├── CodeBuild

├── CodePipeline

├── IAM

└── Inspector
```

---

# Most Common Architecture

```text
Developer

↓

GitHub

↓

CodeBuild

↓

Amazon ECR

↓

Amazon ECS

↓

Application Load Balancer

↓

Users
```

---

# ECS Integration

A Task Definition references an ECR image.

```json
"image": "123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api:v2.1.0"
```

During deployment:

```text
Task Starts

↓

Pull Image

↓

Run Container
```

---

# ECS Image Pull Workflow

```text
Task Definition

↓

Image URI

↓

Amazon ECR

↓

Docker Pull

↓

Container Starts
```

---

# Required IAM Role

Amazon ECS requires the:

```text
Task Execution Role
```

The role allows ECS to:

- Pull images
- Retrieve secrets
- Send logs

---

# Required IAM Policy

The Task Execution Role typically includes:

```text
AmazonECSTaskExecutionRolePolicy
```

Permissions include:

- ecr:GetAuthorizationToken
- ecr:BatchGetImage
- ecr:GetDownloadUrlForLayer
- logs:CreateLogStream
- logs:PutLogEvents

---

# Image Pull Process

```text
ECS Task

↓

IAM Authentication

↓

Amazon ECR

↓

Download Layers

↓

Run Container
```

---

# Using ECR with AWS Lambda

Lambda supports container images.

Architecture:

```text
Docker Image

↓

Amazon ECR

↓

AWS Lambda
```

Maximum image size:

```text
10 GB
```

---

# CodeBuild Integration

CI/CD pipeline:

```text
Git Push

↓

CodeBuild

↓

Docker Build

↓

Amazon ECR
```

---

# CodePipeline Workflow

```text
GitHub

↓

CodePipeline

↓

CodeBuild

↓

Amazon ECR

↓

Amazon ECS
```

---

# IAM Security

Amazon ECR uses IAM for authentication.

Example:

```text
IAM User

↓

IAM Policy

↓

Amazon ECR
```

---

# Common IAM Actions

Useful permissions include:

```text
ecr:GetAuthorizationToken
```

```text
ecr:DescribeRepositories
```

```text
ecr:BatchGetImage
```

```text
ecr:PutImage
```

```text
ecr:BatchDeleteImage
```

---

# Least Privilege

Avoid:

```text
ecr:*
```

Prefer:

```text
Pull Only
```

or

```text
Push Only
```

depending on the workload.

---

# Repository Policies

Repository Policies control who can access a repository.

```text
IAM

↓

Repository Policy

↓

Repository
```

---

# View Repository Policy

```bash
aws ecr get-repository-policy \
--repository-name backend-api
```

---

# Apply Repository Policy

```bash
aws ecr set-repository-policy \
--repository-name backend-api \
--policy-text file://policy.json
```

---

# Cross-Account Access

Large organizations often centralize images.

```text
Account A

↓

Amazon ECR

↓

Account B

↓

Amazon ECS
```

Repository Policies make this possible.

---

# Example Cross-Account Architecture

```text
Shared Services Account

↓

Amazon ECR

↓

Development

↓

Testing

↓

Production
```

Every account pulls from one registry.

---

# Cross-Region Access

Amazon ECR supports replication.

```text
Mumbai

↓

Replication

↓

Singapore

↓

London
```

Useful for:

- Disaster Recovery
- Global deployments
- Lower latency

---

# Repository Encryption

Images are encrypted at rest.

Supported options:

```text
AES-256
```

or

```text
AWS KMS
```

---

# Verify Encryption

```bash
aws ecr describe-repositories
```

Review:

```text
Encryption Configuration
```

---

# Private vs Public Repository

| Feature | Private | Public |
|----------|----------|---------|
| Authentication | Required | Optional |
| IAM | Supported | Limited |
| Enterprise Workloads | ✅ | ❌ |
| Internet Access | Restricted | Public |

---

# Image Signing

Production environments often verify image integrity.

Concept:

```text
Image

↓

Signature

↓

Deployment
```

Only trusted images are deployed.

---

# Secure Deployment Workflow

```text
Build

↓

Scan

↓

Approve

↓

Sign

↓

Deploy
```

---

# Vulnerability Workflow

```text
Docker Image

↓

Amazon ECR

↓

Amazon Inspector

↓

Security Report

↓

Deployment Decision
```

---

# Pull Permissions

A service that only runs containers needs:

```text
Read Only
```

Permissions.

It should not have:

```text
Delete Repository
```

or

```text
Push Image
```

---

# Push Permissions

CI/CD systems require:

- Upload layers
- Put image
- Initiate uploads

Developers typically should not push directly to production repositories.

---

# Secure Repository Architecture

```text
Developers

↓

CodePipeline

↓

Amazon ECR

↓

Amazon ECS

↓

Production
```

---

# Repository Isolation

Recommended:

```text
backend-api

payments

orders

inventory

authentication
```

One repository per application.

---

# Multi-Environment Strategy

Separate repositories or tags.

Example:

```text
backend-api-dev

backend-api-test

backend-api-prod
```

or

```text
backend-api

↓

dev

↓

staging

↓

prod
```

---

# Repository Tagging Strategy

Example:

```text
v1.0.0

↓

v1.1.0

↓

v2.0.0
```

Avoid:

```text
latest
```

---

# Common Errors

## AccessDeniedException

Verify:

- IAM Policy
- Repository Policy
- AWS Account

---

## CannotPullContainerError

Verify:

- Image exists
- IAM Task Execution Role
- Authentication
- Repository URI

---

## Repository Policy Denied

Review:

- Principal
- Action
- Resource

---

## Invalid Image URI

Verify:

```text
Account

↓

Region

↓

Repository

↓

Tag
```

---

# Production Best Practices

- Enable image scanning.
- Use immutable tags.
- Grant least-privilege IAM permissions.
- Store production images in private repositories.
- Separate repositories by application.
- Use AWS KMS encryption when required.
- Use centralized repositories for multi-account environments.
- Pull images only through CI/CD pipelines.
- Restrict push access to build systems.
- Rotate IAM credentials regularly.

---

# Real-World Workflow

```text
Developer

↓

GitHub

↓

CodeBuild

↓

Amazon ECR

↓

Amazon ECS

↓

Production
```

---

# Architecture Note

```text
Developer
      │
      ▼
GitHub
      │
      ▼
AWS CodeBuild
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

Amazon ECR serves as the secure container image registry at the center of modern AWS container platforms, integrating with CI/CD, ECS, Lambda, IAM, and security services to deliver trusted application deployments.

---

# Interview Note

### Question

**How does Amazon ECS securely pull images from Amazon ECR?**

### Answer

Amazon ECS uses the **Task Execution Role** to authenticate with Amazon ECR. When a task starts, the ECS agent requests an authorization token from Amazon ECR using the Task Execution Role, downloads the required image layers, and starts the container. The Task Execution Role typically includes the managed policy **AmazonECSTaskExecutionRolePolicy**, which grants permissions such as `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, and `ecr:GetDownloadUrlForLayer`.

---

# Key Takeaways

- Amazon ECR integrates natively with ECS, EKS, Lambda, and AWS CI/CD services.
- ECS Tasks use the **Task Execution Role** to pull images securely.
- Repository Policies enable fine-grained and cross-account access control.
- Use private repositories and least-privilege IAM policies for production workloads.
- Amazon ECR supports encryption, replication, and vulnerability scanning.
- Separate repositories by application and avoid mutable production tags.
- Secure image management is a critical part of building production-ready container platforms.