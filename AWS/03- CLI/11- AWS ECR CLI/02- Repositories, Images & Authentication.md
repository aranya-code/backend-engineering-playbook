# Repositories, Images & Authentication

> Learn how to create and manage Amazon ECR repositories, authenticate Docker with Amazon ECR, push and pull container images, understand image tags and digests, configure repository policies, and securely manage container images using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create and manage ECR repositories
- Authenticate Docker with ECR
- Push and pull container images
- Understand image tags and digests
- Configure repository policies
- Inspect images
- Secure repositories for production

---

# Amazon ECR Hierarchy

```text
Amazon ECR Registry

↓

Repository

↓

Image

↓

Layers
```

Every image belongs to a repository.

---

# Repository Naming

Good examples:

```text
backend-api
```

```text
payments-service
```

```text
authentication-service
```

Avoid names like:

```text
test
```

```text
newrepo
```

---

# Create Repository

```bash
aws ecr create-repository \
--repository-name backend-api
```

Example output:

```text
Repository URI

↓

123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api
```

---

# List Repositories

```bash
aws ecr describe-repositories
```

---

# Describe Repository

```bash
aws ecr describe-repositories \
--repository-names backend-api
```

Displays:

- ARN
- URI
- Encryption
- Scan configuration
- Image tag mutability

---

# Delete Repository

```bash
aws ecr delete-repository \
--repository-name backend-api
```

Force delete:

```bash
aws ecr delete-repository \
--repository-name backend-api \
--force
```

---

# Repository URI

Every repository has a unique URI.

Example:

```text
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api
```

Docker pushes and pulls images using this URI.

---

# Docker Authentication

Docker must authenticate before interacting with ECR.

Workflow:

```text
AWS CLI

↓

Authentication Token

↓

Docker Login

↓

Amazon ECR
```

---

# Login to Amazon ECR

```bash
aws ecr get-login-password \
| docker login \
--username AWS \
--password-stdin \
123456789012.dkr.ecr.ap-south-1.amazonaws.com
```

This authentication remains valid for approximately **12 hours**.

---

# Verify Docker Login

```bash
docker info
```

or

```bash
docker login
```

You should see:

```text
Login Succeeded
```

---

# Build Docker Image

Example:

```bash
docker build -t backend-api .
```

---

# View Local Images

```bash
docker images
```

Example:

```text
backend-api

latest
```

---

# Tag Docker Image

Before pushing to ECR:

```bash
docker tag backend-api:latest \
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api:latest
```

---

# Image Workflow

```text
Docker Build

↓

Local Image

↓

Docker Tag

↓

Amazon ECR URI
```

---

# Push Image

```bash
docker push \
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api:latest
```

---

# Push Workflow

```text
Docker Image

↓

Authenticate

↓

Push

↓

Amazon ECR
```

---

# List Images

```bash
aws ecr list-images \
--repository-name backend-api
```

---

# Describe Images

```bash
aws ecr describe-images \
--repository-name backend-api
```

Displays:

- Image tags
- Digest
- Size
- Push timestamp
- Scan status

---

# Pull Image

```bash
docker pull \
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api:latest
```

---

# Pull Workflow

```text
Amazon ECR

↓

Docker Pull

↓

Local Image
```

---

# Delete Image

Delete by tag:

```bash
aws ecr batch-delete-image \
--repository-name backend-api \
--image-ids imageTag=latest
```

Delete by digest:

```bash
aws ecr batch-delete-image \
--repository-name backend-api \
--image-ids imageDigest=sha256:xxxxxxxx
```

---

# Image Tags

Example:

```text
backend-api

│

├── latest

├── v1.0.0

├── v1.1.0

└── v2.0.0
```

---

# Tag Best Practices

Avoid:

```text
latest
```

Prefer:

```text
v1.0.0
```

or

```text
2026-07-12
```

Immutable version tags simplify rollbacks.

---

# Image Digest

Every image has a unique digest.

Example:

```text
sha256:abc123...
```

The digest never changes, even if tags do.

---

# Tag vs Digest

| Tag | Digest |
|------|---------|
| Human readable | Unique identifier |
| Can change | Immutable |
| Used during development | Used in production deployments |

---

# Repository Policies

Repository Policies control access.

Example:

```text
IAM User

↓

Repository Policy

↓

Amazon ECR
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

Repository Policies allow:

```text
AWS Account A

↓

Amazon ECR

↓

AWS Account B
```

Useful for centralized image repositories.

---

# Encryption

Amazon ECR encrypts images at rest.

Supported options:

```text
Encryption

│

├── AES-256

└── AWS KMS
```

---

# Image Tag Mutability

Two options exist:

```text
Mutable
```

Existing tags can be overwritten.

---

```text
Immutable
```

Existing tags cannot be changed.

Recommended for production.

---

# Create Immutable Repository

```bash
aws ecr create-repository \
--repository-name backend-api \
--image-tag-mutability IMMUTABLE
```

---

# Common Errors

## RepositoryNotFoundException

Verify:

- Repository name
- Region
- AWS Account

---

## AccessDeniedException

Verify:

- IAM permissions
- Repository Policy

---

## ImageNotFoundException

Verify:

- Tag
- Digest
- Repository

---

## Docker Push Denied

Possible causes:

- Authentication expired
- Incorrect repository URI
- Missing IAM permissions

---

## No Basic Auth Credentials

Run:

```bash
aws ecr get-login-password
```

Authenticate Docker again.

---

# Production Best Practices

- Create separate repositories for each application.
- Use immutable tags in production.
- Never rely on the `latest` tag.
- Authenticate using IAM Roles whenever possible.
- Enable encryption for sensitive workloads.
- Restrict repository access using IAM and Repository Policies.
- Regularly remove unused images.
- Store Dockerfiles in Git alongside application code.

---

# Real-World Workflow

```text
Developer

↓

Docker Build

↓

Docker Tag

↓

Authenticate

↓

Push to Amazon ECR

↓

Amazon ECS Deployment
```

---

# Architecture Note

```text
Developer
      │
      ▼
Docker Build
      │
      ▼
Amazon ECR Repository
      │
      ├── v1.0.0
      ├── v1.1.0
      └── v2.0.0
              │
              ▼
Amazon ECS Service
```

An Amazon ECR repository stores versioned container images that are consumed by ECS services, enabling repeatable and reliable deployments.

---

# Interview Note

### Question

**Why should production deployments use image digests or immutable tags instead of the `latest` tag?**

### Answer

The `latest` tag is mutable and can be overwritten, making deployments unpredictable and difficult to reproduce. Immutable version tags (such as `v2.1.0`) or image digests (`sha256:...`) uniquely identify a specific image version, ensuring consistent deployments, easier rollbacks, and better traceability in CI/CD pipelines.

---

# Key Takeaways

- Repositories organize related container images.
- Docker must authenticate with Amazon ECR before pushing or pulling images.
- Image tags are human-readable, while image digests uniquely identify image content.
- Immutable tags improve deployment reliability.
- Repository Policies provide fine-grained access control.
- Amazon ECR encrypts images at rest and integrates with IAM for secure authentication.
- Proper image versioning is essential for production-grade container deployments.