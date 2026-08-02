# CI-CD & Infrastructure as Code

## Overview

Modern APIs should never be deployed manually.

Production deployments should be:

- Automated
- Repeatable
- Version controlled
- Testable
- Auditable

Continuous Integration (CI), Continuous Deployment (CD), and Infrastructure as Code (IaC) ensure that applications and infrastructure are deployed consistently with minimal human intervention.

For Amazon API Gateway, this means not only deploying application code but also managing:

- APIs
- Stages
- Custom Domains
- Usage Plans
- Authorizers
- Resource Policies
- WAF Associations

using code instead of manual configuration.

---

# What is CI/CD?

CI/CD consists of two major practices.

```text
Developer

↓

Git Push

↓

Continuous Integration

↓

Continuous Deployment

↓

Production
```

---

# Continuous Integration (CI)

CI focuses on validating every code change.

Typical CI pipeline:

```text
Developer

↓

Git Push

↓

Build

↓

Run Tests

↓

Security Scan

↓

Artifact
```

Every commit is automatically verified.

---

# Continuous Deployment (CD)

After CI succeeds:

```text
Artifact

↓

Deploy

↓

Staging

↓

Approval

↓

Production
```

Deployments become automated and repeatable.

---

# Why Automate Deployments?

Manual deployments often lead to:

- Human error
- Configuration drift
- Downtime
- Inconsistent environments

Automation ensures:

```text
Same Code

↓

Same Deployment

↓

Every Environment
```

---

# Infrastructure as Code (IaC)

Infrastructure is described using code.

Instead of:

```text
AWS Console

↓

Manual Clicks
```

Use:

```text
CloudFormation

↓

Deploy
```

Infrastructure becomes reproducible.

---

# Benefits of IaC

Infrastructure becomes:

- Version controlled
- Repeatable
- Reviewable
- Auditable
- Easy to recover

Everything can be recreated from source control.

---

# Common IaC Tools

AWS supports:

- AWS CloudFormation
- AWS CDK
- Terraform
- OpenAPI (for API definitions)

Choose the tool that aligns with your team's standards.

---

# API Gateway as Code

Instead of manually creating:

- APIs
- Routes
- Stages
- Authorizers

Define them declaratively.

```text
Template

↓

Deploy

↓

API Gateway
```

---

# Source Control

Store everything in Git.

Example:

```text
Repository

│

├── Application

├── Infrastructure

├── API Definitions

└── CI Pipeline
```

Infrastructure changes are reviewed like application code.

---

# Environment Strategy

Typical environments:

```text
Development

↓

Testing

↓

Staging

↓

Production
```

Each environment should use the same deployment process.

---

# Branch Strategy

Example:

```text
Feature Branch

↓

Pull Request

↓

Main Branch

↓

Deployment
```

Avoid deploying directly from feature branches.

---

# Pull Requests

Every infrastructure change should be reviewed.

Example:

```text
Developer

↓

Pull Request

↓

Code Review

↓

Merge

↓

Deploy
```

Peer reviews reduce deployment risks.

---

# Automated Testing

Pipeline stages commonly include:

```text
Build

↓

Unit Tests

↓

Integration Tests

↓

Security Tests

↓

Deploy
```

Failed tests stop deployments.

---

# API Testing

Validate:

- Status codes
- Authentication
- Request validation
- Response format
- Performance

Automated API tests help detect regressions early.

---

# Security Scanning

Pipeline should scan for:

- Vulnerable dependencies
- Hardcoded secrets
- Misconfigured IAM
- Container vulnerabilities

Security should be integrated into the pipeline rather than performed only before releases.

---

# Deploy to Staging First

Never deploy directly to production.

```text
Development

↓

Staging

↓

Production
```

Validate changes before exposing them to users.

---

# Canary Deployments

Instead of:

```text
100%

New Version
```

Use:

```text
5%

↓

10%

↓

25%

↓

50%

↓

100%
```

Monitor application health before increasing traffic.

---

# Blue-Green Deployments

Maintain two environments.

```text
Blue

↓

Current

-------------------

Green

↓

New Version
```

Switch traffic after validation.

Benefits:

- Fast rollback
- Minimal downtime

---

# Rollback Strategy

Every deployment should support rollback.

```text
Version 5

↓

Deploy

↓

Issue Found

↓

Rollback

↓

Version 4
```

Rollback should be automated whenever possible.

---

# Configuration Management

Separate configuration from code.

Store:

- Database URLs
- API Keys
- Secrets
- Environment Variables

Use:

- AWS Systems Manager Parameter Store
- AWS Secrets Manager

Avoid hardcoding configuration values.

---

# Secrets Management

Never commit secrets.

Bad:

```python
API_KEY = "abc123"
```

Good:

```text
Secrets Manager

↓

Application
```

Rotate secrets regularly.

---

# Monitor Deployments

After deployment, monitor:

- Error rate
- Latency
- 4XX errors
- 5XX errors
- CPU
- Memory

Deployment is successful only if the application remains healthy.

---

# Infrastructure Drift

Infrastructure drift occurs when production changes differ from source code.

Example:

```text
AWS Console

↓

Manual Change

↓

Code Outdated
```

Avoid manual production changes whenever possible.

---

# Production Deployment Workflow

```text
Developer

↓

GitHub

↓

GitHub Actions

↓

Build

↓

Unit Tests

↓

Security Scan

↓

Deploy to Staging

↓

Integration Tests

↓

Approval

↓

Deploy to Production
```

Every step should be automated.

---

# API Deployment Architecture

```text
Developer

↓

Git Repository

↓

CI/CD Pipeline

↓

CloudFormation / Terraform

↓

API Gateway

↓

Lambda / ECS

↓

CloudWatch Monitoring
```

Infrastructure and application deployments work together.

---

# Common CI/CD Mistakes

Avoid:

- Manual production deployments
- Skipping automated tests
- Hardcoded secrets
- Deploying directly to production
- No rollback strategy
- Editing infrastructure manually
- Missing deployment approvals
- Ignoring post-deployment monitoring

---

# Production Checklist

Before deployment:

- Code reviewed
- Tests passed
- Infrastructure validated
- Secrets managed securely
- Security scan completed
- Deployment automated
- Rollback verified
- Monitoring enabled
- Alerts configured
- Documentation updated

---

# Common Interview Questions

### Why is Infrastructure as Code important?

Infrastructure as Code makes infrastructure reproducible, version controlled, reviewable, and easier to recover, eliminating manual configuration errors.

---

### What is the difference between Continuous Delivery and Continuous Deployment?

Continuous Delivery automatically prepares software for release but may require manual approval before production deployment. Continuous Deployment automatically releases every successful change to production without manual intervention.

---

### Why should infrastructure be stored in Git?

Version control provides change history, peer reviews, rollback capability, collaboration, and auditability for infrastructure changes.

---

### What deployment strategy minimizes production risk?

Canary and Blue-Green deployments minimize risk by gradually shifting traffic or maintaining two production environments for fast rollback.

---

### What should happen if automated tests fail?

The deployment pipeline should stop immediately. Code should never be deployed if quality or security checks fail.

---

# Key Takeaways

- CI/CD automates the build, testing, and deployment of applications and infrastructure.
- Infrastructure as Code ensures AWS resources such as API Gateway are version controlled, reproducible, and easy to manage.
- Automated testing, security scanning, staged deployments, and rollback strategies reduce production risk.
- Secrets and configuration should be managed securely using dedicated AWS services rather than hardcoded values.
- A mature CI/CD pipeline enables reliable, repeatable, and auditable deployments for enterprise-grade APIs.