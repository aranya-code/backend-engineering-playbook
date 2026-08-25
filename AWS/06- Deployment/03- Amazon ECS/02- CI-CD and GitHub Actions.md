# ECS CI/CD and GitHub Actions

# Why CI/CD Matters

Modern software delivery requires:

```text
Fast Releases
Reliable Releases
Repeatable Releases
```

Manual deployments are:

- Slow
- Error-prone
- Difficult to scale

CI/CD solves these problems.

---

# What is CI?

Continuous Integration (CI) means:

```text
Every Code Change
      ↓
Automatically Tested
```

Benefits:

- Early bug detection
- Consistent quality
- Faster feedback

---

# What is CD?

Continuous Delivery / Deployment means:

```text
Code Changes
      ↓
Automatically Deployed
```

to target environments.

---

# ECS CI/CD Architecture

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
ECS Deployment
```

---

# Typical Deployment Workflow

```text
Git Push
    ↓
Run Tests
    ↓
Build Docker Image
    ↓
Push To ECR
    ↓
Update ECS Service
```

---

# Why GitHub Actions?

Benefits:

- Native GitHub integration
- Easy automation
- Secrets management
- Reusable workflows

---

# GitHub Actions Components

Core concepts:

```text
Workflow
Jobs
Steps
Actions
Runners
```

---

# Workflow

Workflow = automation definition.

Example:

```yaml
.github/workflows/deploy.yml
```

---

# Jobs

A workflow contains jobs.

Example:

```text
Test Job
Build Job
Deploy Job
```

---

# Steps

Jobs contain steps.

Example:

```text
Checkout Code
Run Tests
Build Image
```

---

# Runners

Runners execute workflows.

Examples:

```text
Ubuntu
Windows
macOS
```

---

# Docker Build Process

Application:

```text
FastAPI
Django
Node.js
```

---

Build:

```bash
docker build -t app:v1 .
```

---

Result:

```text
Docker Image
```

---

# Amazon ECR

Elastic Container Registry stores images.

Architecture:

```text
Docker Image
      ↓
Amazon ECR
      ↓
ECS Pulls Image
```

---

# Why ECR?

Benefits:

- Managed registry
- IAM integration
- Security scanning
- High availability

---

# Image Versioning

Always version images.

Good:

```text
v1.0.0
v1.0.1
v1.1.0
```

---

Avoid:

```text
latest
```

---

# Why Avoid latest?

Problems:

- Difficult rollbacks
- Unpredictable deployments
- Audit challenges

---

# Deployment Workflow

```text
Code Change
      ↓
Build Image
      ↓
Push To ECR
      ↓
Update Task Definition
      ↓
Deploy ECS Service
```

---

# ECS Deployment Process

ECS deployment consists of:

```text
New Task Definition Revision
        ↓
Service Update
        ↓
Rolling Deployment
```

---

# Task Definition Updates

New image:

```text
v1.2.0
```

Requires:

```text
Task Definition Revision
```

---

Example

```text
user-service:5
```

becomes:

```text
user-service:6
```

---

# Automated Testing

Tests should run before deployment.

Examples:

```text
Unit Tests
Integration Tests
API Tests
```

---

# Example Pipeline

```text
Code Push
      ↓
Tests Pass
      ↓
Deploy
```

---

If tests fail:

```text
Deployment Blocked
```

---

# Security Scanning

Scan images before deployment.

Examples:

```text
Vulnerability Scan
Dependency Scan
Secret Detection
```

---

# Why Security Scanning?

Prevents:

- Vulnerable libraries
- Exposed credentials
- Known CVEs

---

# ECR Image Scanning

Amazon ECR supports:

```text
Image Vulnerability Scanning
```

---

Workflow

```text
Image Push
      ↓
Scan
      ↓
Report Findings
```

---

# GitHub Secrets

Never store credentials in code.

Bad:

```yaml
AWS_SECRET_KEY=abc123
```

---

Use:

```text
GitHub Secrets
```

---

Examples

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

---

# OIDC Authentication

Modern best practice.

Instead of:

```text
Long-Term Credentials
```

Use:

```text
GitHub OIDC
```

---

Benefits:

- More secure
- Short-lived credentials
- Reduced secret management

---

# Deployment Strategies

Common approaches:

```text
Rolling
Blue/Green
Canary
```

---

# Rolling Deployments

Default ECS deployment method.

Benefits:

- Simpler
- Lower cost

---

# Blue/Green Deployments

Supported through:

```text
CodeDeploy
```

---

Benefits:

- Safer releases
- Instant rollback

---

# Rollback Strategy

Bad deployment:

```text
Version 2
```

Fails.

---

Rollback:

```text
Version 1
```

Restore service quickly.

---

# Production Pipeline Example

```text
Git Push
    ↓
Lint
    ↓
Tests
    ↓
Build Image
    ↓
Security Scan
    ↓
Push ECR
    ↓
Deploy ECS
    ↓
Smoke Tests
```

---

# Smoke Testing

After deployment:

Verify:

```text
API Health
Database Connectivity
Critical Endpoints
```

---

# Multi-Environment Deployment

Typical environments:

```text
Development
QA
Staging
Production
```

---

Workflow

```text
Dev
 ↓
QA
 ↓
Staging
 ↓
Production
```

---

# Approval Gates

Production deployments often require:

```text
Manual Approval
```

before release.

---

# Infrastructure as Code

CI/CD should integrate with:

```text
CloudFormation
Terraform
CDK
```

---

Benefits:

- Repeatability
- Version control
- Auditing

---

# Monitoring Deployments

Monitor:

```text
Deployment Status
Task Health
Error Rates
Latency
```

after release.

---

# Production Best Practices

## Automate Everything

Reduce manual work.

---

## Run Tests Before Deployment

Prevent bad releases.

---

## Version Images

Support rollbacks.

---

## Scan Images

Improve security.

---

## Use OIDC

Avoid long-term credentials.

---

## Monitor Releases

Catch problems early.

---

# Common Mistakes

## Using latest Tags

Rollback becomes difficult.

---

## Deploying Without Tests

Increased outage risk.

---

## Hardcoded Credentials

Security risk.

---

## No Rollback Plan

Longer incidents.

---

## Skipping Security Scans

Vulnerabilities reach production.

---

# Troubleshooting

## Deployment Failed

Check:

```text
GitHub Actions Logs
```

---

## ECS Service Not Updating

Check:

```text
Task Definition Revision
```

---

## Image Pull Errors

Check:

```text
ECR Permissions
Execution Role
```

---

## Tests Passing But Deployment Fails

Check:

```text
Environment Variables
Networking
Database Connectivity
```

---

# Common Interview Questions

## What is CI/CD?

Automated build, test, and deployment pipeline.

---

## Why Use GitHub Actions?

Automate workflows directly from GitHub.

---

## Why Use ECR?

Managed container registry.

---

## Why Avoid latest Tags?

Unpredictable deployments.

---

## How Would You Roll Back ECS?

Deploy previous task definition revision.

---

## Why Use OIDC?

Avoid long-term AWS credentials.

---

# Senior Engineer Perspective

CI/CD is not merely automation.

It is a mechanism for:

- Reliability
- Repeatability
- Security
- Faster Delivery

The best deployment pipeline makes deployments:

```text
Boring
```

because predictable deployments reduce operational risk.

Senior engineers invest heavily in automation because every manual step eventually becomes a failure point.

---

# Key Takeaways

- CI/CD automates testing and deployment.
- GitHub Actions integrates well with ECS.
- ECR stores container images.
- Task Definition revisions drive deployments.
- Image versioning is critical.
- OIDC is preferred over long-term credentials.
- Strong CI/CD pipelines improve reliability and release velocity.
