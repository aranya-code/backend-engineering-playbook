# Introduction to ECR CLI

> Learn how to store, secure, manage, and distribute Docker container images using Amazon Elastic Container Registry (Amazon ECR) and the AWS Command Line Interface (AWS CLI). This chapter introduces ECR architecture, repositories, images, registries, authentication, and the core CLI commands required to work with container images in AWS.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon ECR
- Understand container registries
- Create and manage repositories
- Authenticate Docker with ECR
- Push and pull container images
- Understand image lifecycle
- Build a foundation for container deployments

---

# Why Learn Amazon ECR?

Containerized applications require a secure location to store Docker images.

Instead of storing images locally:

```text
Docker Build

↓

Local Image
```

Production deployments require:

```text
Docker Build

↓

Amazon ECR

↓

Amazon ECS

↓

Running Containers
```

Amazon ECR provides a managed, secure container registry integrated with AWS.

---

# What is Amazon ECR?

Amazon Elastic Container Registry (Amazon ECR) is AWS's fully managed container image registry.

It enables you to:

- Store Docker images
- Version images
- Secure repositories
- Scan images
- Replicate images
- Integrate with ECS, EKS, and Lambda

---

# ECR Architecture

```text
Amazon ECR

│

├── Registry

├── Repository

└── Images
```

---

# Registry

Every AWS account automatically receives one private ECR registry.

```text
AWS Account

↓

Amazon ECR Registry

↓

Repositories
```

---

# Repository

A Repository stores related Docker images.

Example:

```text
web-api

↓

v1.0

↓

v1.1

↓

latest
```

---

# Images

Each Docker image consists of:

- Layers
- Metadata
- Tags

```text
Repository

↓

Image

↓

Layers
```

---

# Image Tags

Typical tags:

```text
latest
```

```text
v1.0.0
```

```text
v2.3.1
```

Avoid relying solely on `latest` in production.

---

# Public vs Private ECR

Amazon ECR provides:

```text
Amazon ECR

│

├── Private

└── Public
```

Private repositories are most common for enterprise workloads.

---

# ECR Workflow

```text
Docker Build

↓

Docker Image

↓

Amazon ECR

↓

Amazon ECS

↓

Application
```

---

# ECR CLI Namespace

Amazon ECR uses:

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

# Verify AWS Identity

```bash
aws sts get-caller-identity
```

---

# List Repositories

```bash
aws ecr describe-repositories
```

---

# Create Repository

```bash
aws ecr create-repository \
--repository-name web-api
```

---

# Describe Repository

```bash
aws ecr describe-repositories \
--repository-names web-api
```

---

# Delete Repository

```bash
aws ecr delete-repository \
--repository-name web-api
```

Force delete:

```bash
aws ecr delete-repository \
--repository-name web-api \
--force
```

---

# Global CLI Options

Examples:

```bash
aws ecr describe-repositories \
--profile production
```

```bash
aws ecr describe-repositories \
--region ap-south-1
```

---

# Production Tip

A common production workflow is:

```text
Developer

↓

Docker Build

↓

Amazon ECR

↓

Amazon ECS

↓

Application Load Balancer

↓

Users
```

Never deploy images directly from a developer laptop.

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
      ▼
Amazon ECS Service
      │
      ▼
Running Containers
```

Amazon ECR serves as the secure image registry for container platforms such as Amazon ECS, Amazon EKS, and AWS Lambda.

---

# Interview Note

### Question

**What is Amazon ECR?**

### Answer

Amazon Elastic Container Registry (Amazon ECR) is AWS's fully managed container image registry used to securely store, version, scan, and distribute Docker images. It integrates with Amazon ECS, Amazon EKS, AWS Lambda, IAM, and CI/CD services to simplify container image management.

---

# Key Takeaways

- Amazon ECR is AWS's managed container registry.
- Every AWS account has a private ECR registry.
- Repositories organize related container images.
- Images are identified by tags and digests.
- ECR integrates natively with ECS, EKS, and Lambda.
- The AWS CLI uses the `aws ecr` namespace.
- Amazon ECR is the standard image registry for production AWS container platforms.