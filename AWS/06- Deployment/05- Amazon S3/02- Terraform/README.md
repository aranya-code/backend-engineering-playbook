# README

## Overview

Terraform for Amazon S3 covers the project structure, resource configuration, state management, module design, environment separation, and testing patterns required to deploy and maintain S3 infrastructure reliably using Terraform. It addresses the full Terraform workflow from provider configuration through bucket resource definition, security controls, lifecycle and replication deployment, remote state, reusable modules, multi-environment management, plan review, import of existing resources, drift detection, safe destruction, and validation.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers and platform teams who use Terraform to provision and manage Amazon S3 infrastructure as part of production backend systems.

The focus is on practical Terraform engineering: structuring projects for maintainability, deploying S3 resources with complete and correct configuration, managing state safely across teams, and building reusable module abstractions that enforce consistent security and operational standards.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Terraform Project Structure for S3](./01-%20Terraform%20Project%20Structure%20for%20S3.md) | Reproducible, maintainable project layout for S3 infrastructure across multiple environments |
| 02 | [02- AWS Provider and Version Constraints](./02-%20AWS%20Provider%20and%20Version%20Constraints.md) | AWS provider configuration, version pinning, and managing provider upgrades safely |
| 03 | [03- S3 Bucket Resource Configuration](./03-%20S3%20Bucket%20Resource%20Configuration.md) | `aws_s3_bucket` resource lifecycle, core configuration, and associated resource management |
| 04 | [04- Versioning and Object Ownership Deployment](./04-%20Versioning%20and%20Object%20Ownership%20Deployment.md) | Deploying versioning enablement, Object Ownership controls, and ACL disablement through Terraform |
| 05 | [05- Encryption and KMS Configuration](./05-%20Encryption%20and%20KMS%20Configuration.md) | Server-side encryption configuration, KMS key provisioning, and Bucket Key deployment |
| 06 | [06- Bucket Policies and Public Access Controls](./06-%20Bucket%20Policies%20and%20Public%20Access%20Controls.md) | Deploying bucket policies, Block Public Access settings, and access control as infrastructure code |
| 07 | [07- Lifecycle and Replication Deployment](./07-%20Lifecycle%20and%20Replication%20Deployment.md) | Lifecycle rule configuration, storage class transitions, expiration, and cross-region replication deployment |
| 08 | [08- Remote State and State Locking](./08-%20Remote%20State%20and%20State%20Locking.md) | S3-backed remote state, DynamoDB state locking, and safe state management across teams |
| 09 | [09- Modules and Reusable S3 Components](./09-%20Modules%20and%20Reusable%20S3%20Components.md) | Encapsulating S3 bucket configuration, security controls, and operational settings in reusable modules |
| 10 | [10- Development Staging and Production Environments](./10-%20Development%20Staging%20and%20Production%20Environments.md) | Managing separate environments with workspace or directory-based separation and per-environment configuration |
| 11 | [11- Terraform Plan Review and Apply](./11-%20Terraform%20Plan%20Review%20and%20Apply.md) | Reviewing plan output, interpreting proposed changes, and safely applying infrastructure updates |
| 12 | [12- Importing Existing S3 Resources](./12-%20Importing%20Existing%20S3%20Resources.md) | Importing manually created or script-deployed S3 resources into Terraform state management |
| 13 | [13- State Drift Detection and Reconciliation](./13-%20State%20Drift%20Detection%20and%20Reconciliation.md) | Detecting divergence between Terraform state and actual AWS infrastructure, and reconciliation strategies |
| 14 | [14- Terraform Destroy and Resource Protection](./14-%20Terraform%20Destroy%20and%20Resource%20Protection.md) | Safely decommissioning S3 resources, `prevent_destroy` lifecycle rules, and data protection before deletion |
| 15 | [15- Terraform Testing and Validation](./15-%20Terraform%20Testing%20and%20Validation.md) | Validating syntax, security configuration, and infrastructure behavior through static analysis and automated tests |

## Why Terraform for S3 Matters

Terraform provides repeatable, reviewable, and version-controlled S3 infrastructure deployments. Without it, buckets are created manually with inconsistent configuration, security controls are applied ad hoc, and infrastructure cannot be reliably reproduced or audited.

Common Terraform deployment risks include:

- State file corruption or lock failures that leave infrastructure in a partially reconciled state.
- Plan output not reviewed before apply, causing unintended resource replacements or deletions on production buckets.
- Encryption, versioning, or public access settings not deployed because they were defined separately from the bucket resource and applied out of order.
- Module designs that do not enforce security defaults, allowing callers to omit encryption, Block Public Access, or lifecycle policies.
- Drift between Terraform state and actual infrastructure that goes undetected until a subsequent plan produces unexpected changes.
- `terraform destroy` executed against production resources without `prevent_destroy` protection, resulting in data loss.

Effective Terraform S3 deployment combines a structured project layout, complete resource configuration, safe state management, reusable modules with secure defaults, multi-environment discipline, and automated validation.

## Documentation Structure

This section is organized into focused documents covering the full Terraform lifecycle for S3 from initial project setup through destruction and testing.

| Area | Primary focus |
|---|---|
| Project structure | Layout, organization, and maintainability across environments |
| Provider configuration | AWS provider setup and version management |
| Resource configuration | Core bucket resource and associated configuration resources |
| Security configuration | Versioning, ownership, encryption, KMS, bucket policies, and public access |
| Lifecycle and replication | Transition rules, expiration, and cross-region replication |
| State management | Remote state backend, locking, and safe team workflows |
| Modules | Reusable encapsulations with enforced security defaults |
| Multi-environment | Workspace or directory separation and per-environment config |
| Plan and apply | Safe change review and execution workflow |
| Import, drift, destroy | Managing existing resources, detecting drift, and safe destruction |
| Testing | Static analysis, security scanning, and infrastructure behavior validation |

## Core Terraform Principles for S3

### Always Use Remote State with Locking

Local Terraform state is unsuitable for team environments. Use an S3-backed remote state with DynamoDB state locking. Configure the state bucket itself with versioning and access controls before using it to manage other S3 resources.

### Review the Plan Before Every Apply

Never run `terraform apply` without reviewing the plan output. Pay particular attention to resource replacements — a replacement destroys and recreates the resource, which for an S3 bucket means the bucket must be empty first. Treat unexpected replacements as blockers until the cause is understood.

### Protect Production Buckets from Accidental Deletion

Add `lifecycle { prevent_destroy = true }` to production bucket resources. This prevents `terraform destroy` from deleting the bucket unless the protection is explicitly removed. Combine with a non-empty bucket guard or manual emptying procedure for intentional decommissioning.

### Enforce Security Defaults in Modules

Modules should enable Block Public Access, default encryption, versioning, and lifecycle policies by default. Callers should opt out explicitly with justification rather than having to opt in. This reduces the risk of misconfigured buckets deployed by teams unfamiliar with S3 security requirements.

### Pin Provider Versions

Pin the AWS provider version using a `required_providers` block with an exact or constrained version. Unpinned providers can be upgraded automatically, introducing breaking changes or unexpected resource drift between deployments.

## Recommended Terraform Workflow

1. **Structure the project.** Organize configuration into environment directories or workspaces with a consistent module structure.
2. **Configure the provider.** Pin the AWS provider version. Configure credentials, region, and the remote state backend.
3. **Define resources.** Write bucket, encryption, versioning, public access, lifecycle, and policy resources. Declare dependencies explicitly.
4. **Run `terraform validate`.** Validate syntax and configuration before planning.
5. **Run `terraform plan`.** Review the proposed changes in detail. Confirm no unexpected replacements or deletions are included.
6. **Apply to non-production first.** Execute in development or staging. Validate the deployed configuration.
7. **Promote to production.** Apply to production after non-production validation. Monitor for errors.
8. **Run drift detection.** Schedule regular `terraform plan` or `terraform refresh` runs to detect configuration drift between deployments.

## Operational Standards

- **Remote state:** Use S3-backed remote state with DynamoDB locking for all shared environments.
- **Version pinning:** Pin the AWS provider version in every project.
- **Plan review:** Review plan output before every apply. Treat replacements on production resources as blockers until investigated.
- **prevent_destroy:** Add `lifecycle { prevent_destroy = true }` to production bucket resources.
- **Module defaults:** Enforce Block Public Access, encryption, versioning, and lifecycle policies as module defaults.
- **Environment separation:** Use separate state files, directories, or workspaces for development, staging, and production.
- **Validation:** Run `terraform validate`, static analysis tools, and security scanners in CI before merging IaC changes.
- **Drift detection:** Schedule automated drift detection runs and investigate deviations from the expected state.

## Key Takeaways

- Terraform provides reproducible, reviewable S3 infrastructure deployments but requires disciplined state management, plan review, and module design to be safe in production.
- Remote state with DynamoDB locking is required for any team environment; local state is unsuitable for shared infrastructure.
- Plan review before every apply is the primary control for catching unintended replacements, deletions, or configuration changes.
- `prevent_destroy` lifecycle protection on production buckets prevents accidental data loss from `terraform destroy` execution.
- Modules that enforce security defaults reduce the risk of misconfigured buckets deployed by teams unfamiliar with S3 security requirements.
