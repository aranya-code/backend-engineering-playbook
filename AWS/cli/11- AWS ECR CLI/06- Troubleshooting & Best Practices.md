# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon ECR repositories, authentication, image pushes, replication, image scanning, lifecycle policies, and production deployments. This chapter covers common ECR errors, debugging workflows, IAM troubleshooting, Docker authentication issues, and enterprise best practices for managing container images.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot Amazon ECR repositories
- Debug Docker authentication
- Resolve image push and pull failures
- Troubleshoot image scanning
- Diagnose replication issues
- Secure repositories
- Apply enterprise image management practices

---

# ECR Troubleshooting Workflow

When an image deployment fails:

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

Always troubleshoot from Docker toward the deployment target.

---

# Verify AWS Identity

Before troubleshooting:

```bash
aws sts get-caller-identity
```

Verify:

- AWS Account
- IAM User
- IAM Role

---

# Verify Repository

List repositories.

```bash
aws ecr describe-repositories
```

Describe repository.

```bash
aws ecr describe-repositories \
--repository-names backend-api
```

Verify:

- Repository exists
- Repository URI
- Encryption
- Scan configuration

---

# Verify Repository URI

A common cause of deployment failures is an incorrect URI.

Correct format:

```text
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend-api
```

Verify:

- Account ID
- Region
- Repository Name

---

# Docker Authentication Issues

Authenticate Docker.

```bash
aws ecr get-login-password \
| docker login \
--username AWS \
--password-stdin \
123456789012.dkr.ecr.ap-south-1.amazonaws.com
```

Authentication expires after approximately:

```text
12 Hours
```

---

# Docker Login Failed

Possible causes:

- Wrong AWS Account
- Incorrect Region
- Expired credentials
- Invalid IAM permissions

---

# Verify Docker Login

```bash
docker info
```

Expected:

```text
Login Succeeded
```

---

# Push Failure

Example:

```text
docker push

↓

Denied
```

Verify:

- Repository exists
- Authentication
- IAM permissions
- Repository URI

---

# Pull Failure

Example:

```text
docker pull

↓

Access Denied
```

Verify:

- Repository policy
- IAM permissions
- Image tag
- Region

---

# Image Not Found

Verify available images.

```bash
aws ecr list-images \
--repository-name backend-api
```

---

Describe images.

```bash
aws ecr describe-images \
--repository-name backend-api
```

---

# CannotPullContainerError

Common during ECS deployments.

Verify:

```text
Amazon ECS

↓

Task Execution Role

↓

Amazon ECR

↓

Image
```

Check:

- Repository URI
- Image tag
- IAM Role
- Repository Policy

---

# AccessDeniedException

Verify:

- IAM Policy
- Repository Policy
- AWS Account
- AWS Region

---

# RepositoryNotFoundException

Verify:

- Repository name
- Region
- Account

---

# ImageAlreadyExistsException

Occurs when:

```text
Immutable Repository

↓

Existing Tag
```

Solution:

Push a new version.

Example:

```text
v2.0.1
```

instead of

```text
v2.0.0
```

---

# Invalid Image Tag

Avoid:

```text
latest
```

Prefer:

```text
v2.3.1
```

or

```text
sha256:...
```

---

# Image Scan Failed

Verify:

- Scan enabled
- Repository exists
- Image uploaded

Start scan manually.

```bash
aws ecr start-image-scan \
--repository-name backend-api \
--image-id imageTag=v2.0
```

---

# View Scan Findings

```bash
aws ecr describe-image-scan-findings \
--repository-name backend-api \
--image-id imageTag=v2.0
```

Review:

- Critical
- High
- Medium
- Low

---

# Lifecycle Policy Issues

Preview policy.

```bash
aws ecr get-lifecycle-policy-preview \
--repository-name backend-api
```

Verify:

- Selection rules
- Image count
- Tag prefixes

---

# Replication Issues

Verify registry configuration.

```bash
aws ecr describe-registry
```

Check:

- Destination Regions
- IAM permissions
- Replication rules

---

# Repository Policy Issues

View policy.

```bash
aws ecr get-repository-policy \
--repository-name backend-api
```

Review:

- Principal
- Action
- Resource

---

# Cross-Account Access

Verify:

```text
Account A

↓

Repository Policy

↓

Account B
```

The consuming account must also have appropriate IAM permissions.

---

# ECS Cannot Pull Image

Verify:

- Task Execution Role
- Image URI
- Region
- Repository exists
- Image exists
- Network connectivity

---

# Lambda Cannot Pull Image

Verify:

- Lambda Region
- Repository Region
- IAM permissions
- Image URI

---

# CI/CD Push Failed

Review:

```text
GitHub Actions

↓

Docker Login

↓

Docker Build

↓

Docker Push
```

Common causes:

- Expired credentials
- Repository missing
- IAM permissions
- Wrong URI

---

# Docker Build Succeeds but Push Fails

Workflow:

```text
Docker Build

↓

Image

↓

Authentication

↓

Amazon ECR
```

Usually caused by authentication or permissions.

---

# CloudTrail

Amazon ECR API calls are recorded in:

```text
AWS CloudTrail
```

Useful for auditing:

- Repository creation
- Image deletion
- Repository policy changes
- Authentication events

---

# CloudWatch Monitoring

Monitor:

- Push failures
- Pull failures
- Scan findings
- Repository growth
- Replication status

---

# Security Checklist

Verify:

- Private repository
- IAM least privilege
- Immutable tags
- Encryption enabled
- Image scanning enabled
- Lifecycle policies configured

---

# Common Errors

## AccessDeniedException

Review:

- IAM Policy
- Repository Policy

---

## RepositoryNotFoundException

Verify:

- Repository exists
- Region
- Account

---

## ImageNotFoundException

Verify:

- Image tag
- Digest
- Push completed

---

## No Basic Auth Credentials

Authenticate Docker again.

```bash
aws ecr get-login-password
```

---

## Image Scan Not Available

Verify:

- Scan enabled
- Image exists
- Scan completed

---

## Replication Not Working

Verify:

- Registry replication configuration
- Destination Region
- IAM permissions

---

# Production Best Practices

## Use Immutable Tags

Prefer:

```text
v2.4.0
```

Never overwrite production tags.

---

## Enable Image Scanning

Review:

- Critical
- High

before deployment.

---

## Enable Lifecycle Policies

Automatically remove:

- Old images
- Untagged images

---

## Use Least Privilege

Grant:

```text
Read Only
```

for deployment systems.

Grant:

```text
Push
```

only to CI/CD pipelines.

---

## Separate Repositories

Example:

```text
orders

payments

inventory

users
```

Avoid storing unrelated applications together.

---

## Build Images Once

Preferred workflow:

```text
Build

↓

Test

↓

Promote

↓

Deploy
```

Avoid rebuilding for production.

---

## Enable Cross-Region Replication

Supports:

- Disaster Recovery
- Global deployments

---

## Store Dockerfiles in Git

Never modify production Dockerfiles manually.

---

# Real-World Workflow

```text
GitHub

↓

CI/CD

↓

Docker Build

↓

Amazon ECR

↓

Image Scan

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
CI/CD Pipeline
      │
      ▼
Amazon ECR
      │
      ├── Repository Policies
      ├── Image Scanning
      ├── Lifecycle Policies
      ├── Replication
      └── Encryption
              │
              ▼
Amazon ECS / AWS Lambda
```

Amazon ECR is the trusted image repository at the center of AWS container deployments. Secure authentication, automated scanning, lifecycle management, and proper IAM controls are essential for maintaining reliable and secure production workloads.

---

# Interview Note

### Question

**How would you troubleshoot an ECS task that fails with `CannotPullContainerError`?**

### Answer

I would first verify that the referenced image exists in the correct Amazon ECR repository and Region. Next, I would confirm that the ECS **Task Execution Role** has permissions such as `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, and `ecr:GetDownloadUrlForLayer`. I would also validate the repository URI, image tag or digest, repository policy, and network connectivity. Finally, I would review ECS task events and CloudWatch Logs to identify authentication or image download failures.

---

# Key Takeaways

- Troubleshoot Amazon ECR from authentication through deployment.
- Docker authentication tokens expire and must be refreshed periodically.
- Repository URIs, IAM permissions, and image tags are common sources of failures.
- Image scanning and lifecycle policies should be enabled for production repositories.
- Cross-account and cross-region deployments require both IAM permissions and repository policies.
- CloudTrail and CloudWatch provide valuable auditing and monitoring capabilities.
- Secure image management is a foundational part of production-grade container platforms.