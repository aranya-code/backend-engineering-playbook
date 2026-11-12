# README

## Overview

Amazon S3 deployment covers the toolchain, infrastructure-as-code patterns, CI/CD pipelines, security governance, release management, and troubleshooting workflows required to provision and maintain S3 infrastructure reliably across development, staging, and production environments. It addresses deployment fundamentals, Terraform, CloudFormation, CDK, automated pipelines, static website delivery, Lambda and event-driven deployments, deployment security, release validation, rollback, and diagnostic procedures.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers, platform engineers, and DevOps engineers who are responsible for deploying and operating Amazon S3 infrastructure as part of production backend systems.

The focus is on practical deployment engineering: applying IaC consistently, reviewing proposed changes before execution, enforcing security standards in the deployment path, releasing updates safely, and diagnosing deployment failures systematically.

## Navigation

| # | Folder | Description |
|---|---|---|
| 01 | [01- Deployment Fundamentals](./01-%20Deployment%20Fundamentals/) | Deployment lifecycle, IaC principles, toolchain prerequisites, account and region configuration, environment separation, dependency management, and pre-deployment validation |
| 02 | [02- Terraform](./02-%20Terraform/) | Terraform project structure, S3 resource configuration, encryption, lifecycle, remote state, modules, multi-environment management, plan review, drift detection, and testing |
| 03 | [03- AWS CloudFormation](./03-%20AWS%20CloudFormation/) | CloudFormation templates, S3 resource definitions, security configuration, nested stacks, change sets, rollback, drift detection, stack policies, and validation |
| 04 | [04- AWS CDK](./04-%20AWS%20CDK/) | Python CDK project setup, S3 bucket constructs, encryption and security constructs, reusable construct libraries, CDK Assertions testing, and CDK Pipelines |
| 05 | [05- CI-CD and Automated Deployment](./05-%20CI-CD%20and%20Automated%20Deployment/) | Pipeline architecture, GitHub Actions workflows, OIDC federation, IaC deployment pipelines, environment protection, artifact versioning, and drift detection |
| 06 | [06- Static Website Deployment](./06-%20Static%20Website%20Deployment/) | Private S3 origin with CloudFront, OAC configuration, ACM certificates, cache headers, content versioning, cache invalidation, blue-green releases, and smoke testing |
| 07 | [07- Lambda and Event-Driven Application Deployment](./07-%20Lambda%20and%20Event-Driven%20Application%20Deployment/) | Lambda packaging, dependency bundling, S3 event notification ordering, DLQ deployment, aliases, safe function updates, and end-to-end validation |
| 08 | [08- Deployment Security and Governance](./08-%20Deployment%20Security%20and%20Governance/) | Least-privilege deployment roles, permission separation, policy-as-code scanning, public access guardrails, production resource protection, and audit trails |
| 09 | [09- Release Validation and Rollback](./09-%20Release%20Validation%20and%20Rollback/) | Post-deployment validation, access control and encryption verification, smoke tests, infrastructure rollback, application rollback, and production deployment checklist |
| 10 | [10- Deployment Troubleshooting](./10-%20Deployment%20Troubleshooting/) | Diagnosing Terraform state errors, CloudFormation failures, IAM and OIDC permission errors, bucket name conflicts, encryption failures, Lambda packaging errors, and rollback failures |

## Why S3 Deployment Engineering Matters

Creating an S3 bucket through the console is trivial. Deploying S3 infrastructure reliably, securely, and repeatably across multiple environments and teams requires deliberate engineering discipline. Without it, deployments accumulate configuration debt, security controls are applied inconsistently, and failures are difficult to diagnose or reverse.

Common deployment risks include:

- Infrastructure created manually and never brought under IaC, making it impossible to reproduce, audit, or safely modify.
- Plan output not reviewed before apply, causing unintended resource replacements or deletions on production buckets with data.
- Long-lived AWS access keys stored in CI/CD pipelines that accumulate over time and are never rotated.
- Deployment pipelines that apply changes to production without approval gates, allowing untested configurations to reach live systems automatically.
- IaC templates that define only the bucket resource without encryption, Block Public Access, versioning, or lifecycle configuration.
- No post-deployment validation, leaving deployment failures undiscovered until application errors surface them.
- Production resources without deletion protection, vulnerable to accidental removal during routine deployment operations.

Effective S3 deployment engineering combines version-controlled IaC, pre-deployment plan review, OIDC-based short-lived credentials, automated security scanning, environment protection gates, release validation, and documented rollback procedures.

## Documentation Structure

| Area | Primary focus |
|---|---|
| Fundamentals | Prerequisites, IaC principles, environment separation, and dependency management |
| IaC tools | Terraform, CloudFormation, and CDK-specific patterns and workflows |
| Automation | CI/CD pipelines, OIDC credentials, and deployment automation |
| Specialized deployment | Static websites, Lambda event-driven applications |
| Security and governance | Deployment roles, policy enforcement, and audit evidence |
| Validation and recovery | Post-deployment checks, rollback, and troubleshooting |

## Core Deployment Principles

### Everything in Version-Controlled IaC

Every S3 bucket, its security configuration, lifecycle policies, bucket policies, event notifications, and monitoring resources should be defined in version-controlled IaC from the first deployment. Manual console operations are not reproducible, auditable, or safely modifiable at scale.

### Review Before You Apply

Never apply an IaC change without reviewing the proposed changes first. Use `terraform plan`, CloudFormation change sets, or `cdk diff` to inspect what will be created, modified, or destroyed. Treat unexpected resource replacements on production resources as blockers until the cause is understood.

### Use Short-Lived Credentials in Pipelines

Configure CI/CD pipelines to obtain temporary AWS credentials through IAM OIDC federation. Eliminate stored long-lived access keys from pipeline secrets. Short-lived credentials reduce the credential exposure window and provide a clean per-deployment audit trail in CloudTrail.

### Validate After Every Deployment

Run post-deployment validation after every deployment. Verify that bucket configuration, access controls, encryption settings, and application integrations operate correctly. Do not treat a successful apply or stack update as evidence that the deployment is correct.

### Protect Production Resources Explicitly

Apply `prevent_destroy` in Terraform, stack policies in CloudFormation, or CDK removal policies on production bucket resources. Require human approval before production deployments in CI/CD pipelines. Document and test the intentional decommissioning procedure separately from routine operations.

## Key Takeaways

- S3 deployment requires version-controlled IaC, pre-change review, post-deployment validation, and documented rollback procedures — the gap between a working deployment and a production-ready one must be closed deliberately.
- Plan and change set review before every apply is the primary control for catching unintended replacements or deletions before they affect production data.
- OIDC federation for CI/CD credentials eliminates stored key exposure risk and provides a clean per-deployment audit trail.
- Approval gates and deployment security scanning in the pipeline path are the scalable way to enforce security standards without manual review of every change.
- Post-deployment validation is the only reliable way to confirm that infrastructure, security controls, and application integrations are all operating correctly after a change.
