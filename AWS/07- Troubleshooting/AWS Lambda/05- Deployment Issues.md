# 05- Deployment Issues

# Overview

Deploying AWS Lambda is more than uploading code. Every deployment introduces the possibility of runtime failures, missing dependencies, incorrect configurations, permission errors, or traffic disruptions.

Many production outages occur immediately after deployment because of configuration mistakes rather than application bugs.

This chapter covers the most common Lambda deployment issues, explains how to troubleshoot them, and discusses best practices for achieving safe, reliable, and zero-downtime deployments.

---

# Lambda Deployment Workflow

A typical deployment pipeline looks like:

```
Developer

↓

Git

↓

CI/CD Pipeline

↓

Build

↓

Package

↓

Deploy

↓

Publish Version

↓

Update Alias

↓

Production
```

Each stage should include automated validation.

---

# Common Deployment Problems

Typical deployment failures include:

- Deployment package errors
- Missing dependencies
- Handler misconfiguration
- Environment variable issues
- Runtime mismatch
- Version conflicts
- Alias misconfiguration
- IAM permission failures
- Container image problems
- Infrastructure drift

---

# Problem: Deployment Succeeds but Function Fails

Symptoms

```
Deployment Successful

↓

Invocation

↓

Runtime Error
```

Possible causes

- Missing dependency
- Wrong handler
- Incorrect runtime
- Environment variable missing

---

## Investigation

Review

```
CloudWatch Logs

↓

Runtime Exception

↓

Deployment Package
```

---

# Problem: Missing Dependency

Example

```
Runtime.ImportModuleError

Unable to import module
```

Common causes

- Package not included
- Incorrect build environment
- Wrong dependency version

Example

```
requirements.txt

↓

Build

↓

ZIP Package

↓

Lambda
```

Always build packages for the target runtime.

---

# Problem: Incorrect Handler

Example

```
Handler 'app.handler' missing
```

Suppose your file is

```
main.py
```

Function

```python
def lambda_handler(event, context):
```

Correct handler

```
main.lambda_handler
```

Incorrect handler configuration prevents Lambda from starting.

---

# Problem: Runtime Version Mismatch

Example

```
Python 3.12

↓

Dependency supports only 3.10
```

Symptoms

- Import errors
- Runtime crashes
- Unexpected behavior

Always test runtime upgrades before production deployment.

---

# Problem: Environment Variables Missing

Example

```
KeyError

DATABASE_URL
```

Possible causes

- Missing variable
- Wrong variable name
- Incorrect deployment configuration

Verify

```
Configuration

↓

Environment Variables
```

---

# Problem: Lambda Layer Version Changed

Architecture

```
Function

↓

Layer Version

↓

Dependency Missing
```

Possible causes

- Deleted layer
- Wrong version
- Incompatible dependency

Always version Lambda Layers carefully.

---

# Problem: Alias Points to Wrong Version

Example

```
Production Alias

↓

Old Version
```

or

```
Production Alias

↓

Broken Version
```

Verify

```
Alias

↓

Published Version
```

Never point production directly to `$LATEST`.

---

# Problem: Function Version Deleted

Example

```
Version

↓

Deleted

↓

Alias Broken
```

Solution

Publish a new version and update the alias.

---

# Problem: Deployment Package Too Large

Example

```
RequestEntityTooLargeException
```

Solutions

- Remove unnecessary libraries
- Use Lambda Layers
- Use Container Images
- Compress assets

---

# Problem: Container Image Deployment Fails

Example

```
Image Pull Failed
```

Possible causes

- Wrong image tag
- Missing ECR permission
- Deleted image
- Architecture mismatch

Verify

- ECR repository
- Image tag
- IAM permissions

---

# Problem: Architecture Mismatch

Example

```
Built for ARM

↓

Running on x86_64
```

or

```
Built for x86_64

↓

Running on ARM64
```

Always verify the Lambda architecture matches the build target.

---

# Problem: IAM Permission During Deployment

Example

```
AccessDeniedException
```

Required deployment permissions often include

```
lambda:UpdateFunctionCode

lambda:PublishVersion

iam:PassRole
```

Verify CI/CD role permissions.

---

# Problem: Infrastructure Drift

Symptoms

Deployment succeeds but production behaves differently.

Possible causes

- Manual console changes
- Drift from IaC templates
- Missing infrastructure updates

Recommended approach

```
CloudFormation

or

AWS CDK

or

Terraform
```

Treat infrastructure as code.

---

# Problem: Rollback Failure

Example

```
New Version

↓

Errors

↓

Rollback Fails
```

Always keep previous published versions available.

Use aliases for traffic switching.

---

# Zero-Downtime Deployment

Recommended workflow

```
Version 10

↓

Deploy Version 11

↓

Canary

↓

Monitor

↓

100% Traffic
```

If failures occur

```
Alias

↓

Version 10
```

Rollback is immediate.

---

# Canary Deployment

```
10%

↓

25%

↓

50%

↓

100%
```

Benefits

- Reduced production risk
- Early issue detection
- Easier rollback

---

# Blue/Green Deployment

```
Blue

↓

Production

----------------

Green

↓

New Version

↓

Switch Traffic
```

Benefits

- Near-zero downtime
- Instant rollback
- Production validation

---

# Deployment Validation Checklist

Before deployment

- Unit Tests
- Integration Tests
- Security Scan
- Dependency Scan
- Package Validation

After deployment

- Smoke Tests
- CloudWatch Metrics
- CloudWatch Logs
- X-Ray Traces
- API Validation

---

# CloudWatch Verification

After deployment monitor

```
Errors

↓

Duration

↓

Invocations

↓

Throttles
```

Watch for sudden changes.

---

# Common Deployment Mistakes

❌ Deploying directly to production

❌ Using `$LATEST`

❌ Manual console updates

❌ Ignoring CloudWatch

❌ Missing rollback strategy

❌ Large deployment packages

❌ Hardcoded configuration

❌ No automated testing

---

# CI/CD Best Practices

A mature deployment pipeline should include

```
Git Push

↓

Build

↓

Unit Tests

↓

Static Analysis

↓

Security Scan

↓

Package

↓

Deploy

↓

Publish Version

↓

Update Alias

↓

Smoke Test

↓

Production
```

Automation reduces deployment risk.

---

# Real-World Example

A payment service introduces a new Lambda version.

```
Developer

↓

GitHub

↓

GitHub Actions

↓

Build

↓

Deploy Version 15

↓

Alias → 10%

↓

CloudWatch

↓

Healthy

↓

Alias → 100%
```

If errors increase

```
Alias

↓

Version 14
```

Production is restored within seconds.

---

# Best Practices

✅ Always publish immutable versions.

✅ Use aliases instead of `$LATEST`.

✅ Automate deployments using CI/CD.

✅ Validate deployments with smoke tests.

✅ Monitor CloudWatch immediately after deployment.

✅ Keep rollback procedures documented.

✅ Use Infrastructure as Code.

✅ Test runtime upgrades in lower environments first.

---

# Senior Backend Engineering Perspective

Deployment is not merely a release activity—it is a reliability practice. Senior engineers design deployment pipelines that minimize risk through automation, versioning, gradual rollouts, continuous monitoring, and rapid rollback capabilities.

Rather than relying on manual verification, they use immutable deployments, infrastructure as code, automated testing, and observability to ensure that every release is safe, repeatable, and recoverable.

---

# Key Takeaways

- Most Lambda deployment issues arise from configuration, packaging, runtime, or IAM mistakes rather than code defects.
- Immutable versions, aliases, and progressive deployment strategies significantly reduce production risk.
- CI/CD automation, smoke testing, and Infrastructure as Code improve deployment reliability.
- CloudWatch and AWS X-Ray should be used to validate every production deployment.
- Successful deployment strategies prioritize safety, observability, and rapid recovery.