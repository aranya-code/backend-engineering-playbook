# Image Management, Scanning & Lifecycle Policies

> Learn how to manage container images in Amazon ECR using the AWS CLI. This chapter covers image scanning, lifecycle policies, vulnerability management, image cleanup, repository optimization, image replication, and production image management strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Manage container images
- Scan images for vulnerabilities
- Configure lifecycle policies
- Remove unused images
- Optimize repositories
- Manage image versions
- Apply production image management practices

---

# Why Image Management Matters?

Container images continue growing over time.

Example:

```text
Repository

↓

v1.0

↓

v1.1

↓

v1.2

↓

...

↓

v56.0
```

Without cleanup:

- Storage grows
- Costs increase
- Old vulnerabilities remain
- Repository becomes difficult to manage

---

# Image Lifecycle

```text
Build

↓

Push

↓

Scan

↓

Deploy

↓

Retain

↓

Delete
```

---

# View Images

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

- Tags
- Digest
- Push time
- Size
- Scan status

---

# Image Metadata

Example output contains:

```text
Image Tag

↓

v2.1.0
```

```text
Digest

↓

sha256:abc...
```

```text
Size

↓

145 MB
```

---

# Delete an Image

Delete by tag:

```bash
aws ecr batch-delete-image \
--repository-name backend-api \
--image-ids imageTag=v1.0.0
```

---

Delete by digest:

```bash
aws ecr batch-delete-image \
--repository-name backend-api \
--image-ids imageDigest=sha256:xxxxxxxx
```

---

# Delete Multiple Images

```bash
aws ecr batch-delete-image \
--repository-name backend-api \
--image-ids imageTag=v1 imageTag=v2
```

---

# Image Scanning

Amazon ECR can scan container images for known vulnerabilities.

Workflow:

```text
Push Image

↓

Scan

↓

Find Vulnerabilities

↓

Review Report
```

---

# Scan Types

Amazon ECR supports:

```text
Scanning

│

├── Basic Scanning

└── Enhanced Scanning
```

---

# Basic Scanning

Provides:

- CVEs
- Package vulnerabilities
- Severity levels

Suitable for many workloads.

---

# Enhanced Scanning

Uses Amazon Inspector.

Provides:

- Continuous scanning
- New vulnerability detection
- Detailed findings
- Better reporting

Recommended for production.

---

# Enable Scan on Push

```bash
aws ecr put-image-scanning-configuration \
--repository-name backend-api \
--image-scanning-configuration scanOnPush=true
```

Every pushed image is scanned automatically.

---

# Start Manual Scan

```bash
aws ecr start-image-scan \
--repository-name backend-api \
--image-id imageTag=v2.0
```

---

# View Scan Results

```bash
aws ecr describe-image-scan-findings \
--repository-name backend-api \
--image-id imageTag=v2.0
```

---

# Vulnerability Severity

Amazon ECR classifies findings.

```text
Critical
```

```text
High
```

```text
Medium
```

```text
Low
```

```text
Informational
```

---

# Example Scan Workflow

```text
Docker Build

↓

Push

↓

Automatic Scan

↓

Review Findings

↓

Deploy
```

---

# Image Lifecycle Policies

Lifecycle Policies automatically delete old images.

Example:

```text
Repository

↓

100 Images

↓

Keep Latest 20

↓

Delete Remaining
```

---

# Why Lifecycle Policies?

Benefits:

- Lower storage costs
- Cleaner repositories
- Automatic maintenance
- Simpler image management

---

# Lifecycle Policy Structure

Policies define:

- Selection
- Rule priority
- Action

Example:

```text
Rule

↓

Select Images

↓

Expire Images
```

---

# Example Lifecycle Policy

```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep latest 10 images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
```

---

# Apply Lifecycle Policy

```bash
aws ecr put-lifecycle-policy \
--repository-name backend-api \
--lifecycle-policy-text file://policy.json
```

---

# View Lifecycle Policy

```bash
aws ecr get-lifecycle-policy \
--repository-name backend-api
```

---

# Preview Lifecycle Policy

Always preview before applying.

```bash
aws ecr get-lifecycle-policy-preview \
--repository-name backend-api
```

---

# Lifecycle Workflow

```text
Repository

↓

Lifecycle Policy

↓

Expired Images

↓

Automatic Cleanup
```

---

# Untagged Images

Images without tags:

```text
<none>

↓

Unused
```

These are good cleanup candidates.

---

# Keep Latest Images

Example:

```text
Latest 20

↓

Keep

────────────

Older Images

↓

Delete
```

---

# Image Version Strategy

Good example:

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

↓

latest

↓

latest
```

---

# Immutable Images

Production deployments should use:

```text
Immutable Tags
```

Never overwrite production images.

---

# Repository Size

Monitor:

- Number of images
- Storage usage
- Scan findings
- Cleanup status

---

# Storage Optimization

Recommended:

- Delete unused images
- Remove untagged images
- Enable lifecycle policies
- Keep only active versions

---

# Common Errors

## ScanNotFoundException

Verify:

- Image exists
- Scan completed
- Repository name

---

## LifecyclePolicyNotFoundException

Verify:

- Policy applied
- Repository exists

---

## ImageAlreadyExistsException

Occurs when:

```text
Immutable Repository

↓

Existing Tag
```

Push a new version instead.

---

## TooManyImages

Repository contains excessive unused images.

Enable lifecycle policies.

---

# Production Best Practices

- Enable image scanning for every repository.
- Review Critical and High vulnerabilities before deployment.
- Use Enhanced Scanning for production workloads.
- Apply lifecycle policies to every repository.
- Remove untagged images regularly.
- Keep immutable version tags.
- Store Dockerfiles in version control.
- Monitor repository growth over time.

---

# Real-World Workflow

```text
Build Docker Image

↓

Push to ECR

↓

Automatic Scan

↓

Review Findings

↓

Deploy to ECS

↓

Lifecycle Cleanup
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
Amazon ECR
      │
      ├── Image Scan
      ├── Lifecycle Policy
      ├── Vulnerability Report
      └── Image Repository
              │
              ▼
Amazon ECS
```

Amazon ECR not only stores container images but also provides security scanning and automated lifecycle management, helping maintain secure and efficient container repositories.

---

# Interview Note

### Question

**Why should Lifecycle Policies be configured in Amazon ECR?**

### Answer

Lifecycle Policies automatically remove old or unused container images based on configurable rules, such as retaining only the most recent image versions or deleting untagged images. This reduces storage costs, keeps repositories organized, minimizes the risk of deploying outdated images, and simplifies long-term repository maintenance.

---

# Key Takeaways

- Amazon ECR supports both Basic and Enhanced image scanning.
- Enable **scan on push** to detect vulnerabilities automatically.
- Review Critical and High findings before promoting images to production.
- Lifecycle Policies automatically clean up old images.
- Immutable image tags improve deployment reliability.
- Regular repository cleanup reduces storage costs and operational complexity.
- Combining image scanning with lifecycle management creates secure, production-ready container repositories.