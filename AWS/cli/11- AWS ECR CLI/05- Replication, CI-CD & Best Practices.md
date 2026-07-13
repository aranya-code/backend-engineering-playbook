# Replication, CI/CD & Best Practices

> Learn how Amazon ECR supports cross-Region replication, integrates with CI/CD pipelines, automates image delivery, and enables production-ready container workflows. This chapter covers replication, CodeBuild, CodePipeline, GitHub Actions, deployment strategies, repository organization, and enterprise best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Configure image replication
- Understand multi-region image distribution
- Integrate Amazon ECR into CI/CD
- Build automated deployment pipelines
- Design enterprise container workflows
- Optimize image repositories
- Apply production best practices

---

# Why Replication?

Applications often run in multiple AWS Regions.

Without replication:

```text
Mumbai

↓

Amazon ECR

↓

Singapore ECS
```

Images must be pulled across Regions.

With replication:

```text
Mumbai

↓

Replication

↓

Singapore

↓

Local ECR

↓

Amazon ECS
```

Benefits:

- Lower latency
- Faster deployments
- Disaster recovery
- Regional redundancy

---

# Replication Workflow

```text
Push Image

↓

Primary Repository

↓

Automatic Replication

↓

Secondary Repository

↓

Deploy
```

---

# Cross-Region Replication

Amazon ECR automatically copies images.

Example:

```text
Primary

↓

ap-south-1

────────────

Replica

↓

eu-west-1
```

---

# Replication Architecture

```text
Developer

↓

Amazon ECR

↓

Replication

↓

Region A

↓

Region B

↓

Region C
```

---

# Configure Replication

Replication is configured at the registry level.

```bash
aws ecr put-replication-configuration \
--replication-configuration file://replication.json
```

---

# View Replication Configuration

```bash
aws ecr describe-registry
```

---

# Multi-Region Deployment

```text
Users

↓

Route53

↓

Mumbai

↓

Amazon ECS

────────────

Singapore

↓

Amazon ECS
```

Each Region pulls images from its local ECR repository.

---

# Disaster Recovery

If one Region fails:

```text
Mumbai

↓

Unavailable

────────────

Singapore

↓

Replica Images

↓

Deploy
```

Applications continue running.

---

# Amazon ECR in CI/CD

Typical workflow:

```text
Git Push

↓

Build

↓

Docker Image

↓

Amazon ECR

↓

Amazon ECS
```

---

# CI/CD Architecture

```text
Developer

↓

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

# Build Stage

The build server:

```text
Source Code

↓

Docker Build

↓

Docker Image
```

---

# Push Stage

The image is pushed.

```text
Docker Image

↓

Amazon ECR
```

---

# Deploy Stage

```text
Amazon ECR

↓

Amazon ECS

↓

Rolling Deployment
```

---

# CodeBuild Workflow

```text
GitHub

↓

CodeBuild

↓

Docker Build

↓

Docker Push

↓

Amazon ECR
```

---

# BuildSpec Example

Typical workflow inside `buildspec.yml`

```yaml
phases:
  pre_build:
    commands:
      - aws ecr get-login-password
  build:
    commands:
      - docker build
  post_build:
    commands:
      - docker push
```

---

# GitHub Actions Workflow

```text
GitHub

↓

GitHub Actions

↓

Docker Build

↓

Amazon ECR

↓

Amazon ECS
```

---

# Deployment Pipeline

```text
Developer

↓

Git Commit

↓

GitHub

↓

CI/CD

↓

Amazon ECR

↓

Amazon ECS

↓

Users
```

---

# Rolling Deployments

CI/CD updates:

```text
Task Definition

↓

New Revision

↓

Rolling Deployment
```

No downtime.

---

# Blue/Green Deployments

```text
Blue

↓

Current Version

────────────

Green

↓

New Version
```

After validation:

```text
Traffic

↓

Green
```

---

# Canary Deployment

```text
90%

↓

Version 1

────────────

10%

↓

Version 2
```

Traffic gradually shifts.

---

# Image Promotion

Instead of rebuilding:

```text
Development

↓

Testing

↓

Production
```

Promote the same tested image.

---

# Version Workflow

Example:

```text
v2.1.0

↓

QA

↓

Production
```

One immutable image.

---

# Repository Organization

Enterprise example:

```text
Repositories

│

├── api

├── payments

├── orders

├── inventory

└── frontend
```

---

# Environment Strategy

Option 1:

Separate repositories.

```text
backend-dev

backend-test

backend-prod
```

---

Option 2:

Single repository.

```text
backend

↓

dev

↓

staging

↓

production
```

---

# Image Promotion Strategy

```text
v2.0.0

↓

Testing

↓

Approved

↓

Production
```

Avoid rebuilding between environments.

---

# Immutable Deployments

Recommended:

```text
Image

↓

Digest

↓

Deploy
```

Never deploy mutable images.

---

# Cleanup Strategy

Regularly:

- Remove unused images
- Delete untagged images
- Apply lifecycle policies
- Monitor storage

---

# Monitoring

Monitor:

- Repository size
- Image count
- Replication status
- Scan findings
- Failed pushes

---

# Common Errors

## Replication Not Working

Verify:

- Registry configuration
- Destination Region
- IAM permissions

---

## CI/CD Push Failed

Verify:

- Docker login
- Repository exists
- IAM permissions
- Repository URI

---

## Deployment Uses Old Image

Possible causes:

- Mutable tags
- ECS service not updated
- Cached image

Use immutable tags or image digests.

---

## Image Missing

Verify:

- Push completed
- Correct Region
- Replication completed

---

# Production Best Practices

- Enable cross-Region replication for disaster recovery.
- Use immutable image tags.
- Promote tested images instead of rebuilding.
- Build images only in CI/CD pipelines.
- Store Dockerfiles in source control.
- Enable image scanning and lifecycle policies.
- Use separate repositories for independent services.
- Restrict production image pushes to automation only.
- Monitor repository growth and vulnerability reports.
- Keep repositories clean with automated lifecycle policies.

---

# Real-World Workflow

```text
Developer

↓

GitHub

↓

GitHub Actions

↓

Docker Build

↓

Amazon ECR

↓

Image Scan

↓

Amazon ECS

↓

Rolling Deployment

↓

Production
```

---

# Enterprise Architecture

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
      ├── Image Scan
      ├── Lifecycle Policy
      ├── Replication
      └── Immutable Images
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

Amazon ECR acts as the secure image distribution hub for modern cloud-native applications, integrating seamlessly with CI/CD pipelines and Amazon ECS deployments.

---

# Interview Note

### Question

**How is Amazon ECR typically integrated into a CI/CD pipeline?**

### Answer

A CI/CD pipeline typically builds a Docker image after a source code commit, authenticates with Amazon ECR, pushes the image to a repository, optionally performs vulnerability scanning, and then updates the Amazon ECS service with a new Task Definition revision referencing the new image. ECS performs a rolling or Blue/Green deployment, allowing new tasks to become healthy before old tasks are terminated. Using immutable image tags or image digests ensures deployments are repeatable and simplifies rollbacks.

---

# Key Takeaways

- Amazon ECR supports automatic cross-Region replication for high availability and disaster recovery.
- Modern CI/CD pipelines build images once and store them in Amazon ECR.
- Promote tested images across environments instead of rebuilding them.
- Use immutable image tags or digests for predictable deployments.
- Separate repositories by application or service for easier management.
- Enable lifecycle policies and vulnerability scanning for long-term repository health.
- Amazon ECR is a central component of production-grade container delivery pipelines.