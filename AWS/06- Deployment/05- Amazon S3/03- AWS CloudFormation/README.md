# README

## Overview

AWS CloudFormation for Amazon S3 covers the template structure, resource definitions, security configuration, stack composition, change management, rollback, drift detection, and validation workflows required to deploy and maintain S3 infrastructure as declarative CloudFormation templates. It addresses the full CloudFormation deployment lifecycle from initial template design through nested stack composition, parameterization, change set review, stack rollback, drift detection, stack policies, and template testing.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers and platform teams who use CloudFormation to provision and manage Amazon S3 infrastructure as part of production backend systems.

The focus is on practical CloudFormation engineering: writing templates that are complete, secure, and maintainable, reviewing change sets before execution, protecting production resources from unintended updates, detecting and remediating configuration drift, and validating templates before they reach AWS.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- CloudFormation for S3](./01-%20CloudFormation%20for%20S3.md) | CloudFormation as an IaC service for S3, declarative YAML and JSON templates, and S3 resource type overview |
| 02 | [02- Template Structure and Parameters](./02-%20Template%20Structure%20and%20Parameters.md) | CloudFormation template anatomy, parameter definitions, and designing reusable parameterized templates |
| 03 | [03- S3 Bucket and Output Definitions](./03-%20S3%20Bucket%20and%20Output%20Definitions.md) | `AWS::S3::Bucket` resource configuration, output exports, and cross-stack bucket references |
| 04 | [04- Encryption and Access Control Templates](./04-%20Encryption%20and%20Access%20Control%20Templates.md) | Defining encryption settings, KMS key references, bucket policies, and Block Public Access in CloudFormation |
| 05 | [05- Versioning and Lifecycle Templates](./05-%20Versioning%20and%20Lifecycle%20Templates.md) | Versioning configuration, lifecycle rules, storage class transitions, and expiration in CloudFormation |
| 06 | [06- Replication Roles and Policies](./06-%20Replication%20Roles%20and%20Policies.md) | Cross-region replication configuration, IAM replication roles, destination bucket policies, and dependency ordering |
| 07 | [07- Nested Stacks and Stack Composition](./07-%20Nested%20Stacks%20and%20Stack%20Composition.md) | Organizing infrastructure into nested stacks, parent-child relationships, and reusable component templates |
| 08 | [08- Parameters Mappings and Conditions](./08-%20Parameters%20Mappings%20and%20Conditions.md) | Using parameters, mappings, and conditions to build environment-aware and configurable CloudFormation templates |
| 09 | [09- Change Sets and Stack Updates](./09-%20Change%20Sets%20and%20Stack%20Updates.md) | Reviewing proposed changes before execution, interpreting change set output, and safe stack update workflows |
| 10 | [10- Stack Rollback and Failure Recovery](./10-%20Stack%20Rollback%20and%20Failure%20Recovery.md) | Automatic and manual rollback, rollback triggers, failed stack recovery, and ROLLBACK_COMPLETE state resolution |
| 11 | [11- Drift Detection and Remediation](./11-%20Drift%20Detection%20and%20Remediation.md) | Detecting differences between template-defined and actual resource configuration, and remediation strategies |
| 12 | [12- Stack Policies and Resource Protection](./12-%20Stack%20Policies%20and%20Resource%20Protection.md) | Protecting production resources from update or replacement using CloudFormation stack policies |
| 13 | [13- CloudFormation Validation and Testing](./13-%20CloudFormation%20Validation%20and%20Testing.md) | Template syntax validation, security scanning, linting, and deployment testing workflows |

## Why CloudFormation for S3 Matters

CloudFormation provides declarative, AWS-native infrastructure deployments that are reproducible, auditable, and integrated with AWS services. Without it, S3 configuration is applied inconsistently, dependencies are managed manually, and there is no reliable record of what was deployed.

Common CloudFormation deployment risks include:

- Templates that define the bucket resource but omit encryption, Block Public Access, versioning, or lifecycle configuration, leaving security and cost controls unconfigured.
- Stack updates that trigger unintended resource replacements because a property change requires recreation rather than in-place update.
- Missing change set review before stack updates, applying changes to production without confirming the intended scope.
- Nested stack dependencies that cause deployment failures or partial updates when child stacks are updated out of order.
- Drift between template-defined configuration and actual resource state that goes undetected until a stack update behaves unexpectedly.
- Stack policies absent on production stacks, allowing updates to replace or delete critical resources without restriction.

Effective CloudFormation S3 deployment combines complete template definitions, change set review before every update, stack policies on production stacks, drift detection, and automated template validation.

## Documentation Structure

This section is organized into focused documents progressing from template fundamentals through resource configuration, security controls, stack composition, change management, and validation.

| Area | Primary focus |
|---|---|
| Template fundamentals | CloudFormation service, template structure, parameters, and resource types |
| Resource configuration | Bucket definitions, outputs, encryption, versioning, lifecycle, and replication |
| Stack composition | Nested stacks, parameters, mappings, conditions, and reusable templates |
| Change management | Change sets, stack updates, rollback, and failure recovery |
| Drift and protection | Drift detection, stack policies, and resource protection |
| Validation and testing | Template validation, security scanning, and deployment testing |

## Core CloudFormation Principles for S3

### Define Complete Resources

An `AWS::S3::Bucket` resource in CloudFormation creates a bucket with minimal default configuration. Encryption, Block Public Access, versioning, lifecycle rules, and logging must be explicitly defined in the template. A template that defines only the bucket resource without these settings deploys an incompletely configured bucket.

### Always Create and Review a Change Set Before Updating

Create a change set before every stack update. Review the proposed changes in the change set output before executing. Pay particular attention to `Replacement: True` entries — these destroy and recreate the resource, which for S3 requires the bucket to be empty. Do not execute a change set with unexpected replacements without understanding the cause.

### Apply Stack Policies to Production Stacks

CloudFormation stack policies can prevent updates that would modify or replace specific resources. Apply a stack policy to every production stack that protects critical S3 buckets and associated IAM roles from unintended updates or replacements during normal deployments.

### Use Parameters for Environment-Specific Configuration

Use CloudFormation parameters for values that differ between environments, such as bucket names, encryption key ARNs, replication destination buckets, and notification target ARNs. This allows the same template to deploy correctly configured infrastructure across development, staging, and production without modification.

### Enable Drift Detection on a Schedule

CloudFormation drift detection identifies differences between the template and the actual resource configuration. Schedule drift detection runs on production stacks and review findings regularly. Undetected drift produces unexpected plan output during subsequent updates and indicates that resources have been modified outside of CloudFormation.

## Recommended CloudFormation Workflow

1. **Write a complete template.** Define the bucket resource and all associated configuration: encryption, Block Public Access, versioning, lifecycle, policy, and logging.
2. **Validate the template.** Run `aws cloudformation validate-template` and static analysis tools before deployment.
3. **Create a change set.** For any update to an existing stack, create a change set and review the output before executing.
4. **Deploy to non-production.** Deploy to development or staging. Validate the result.
5. **Apply a stack policy.** Add a stack policy to production stacks that prevents unintended resource replacements.
6. **Promote to production.** Create a change set for the production stack. Review and execute.
7. **Run drift detection.** Schedule regular drift detection runs. Investigate any detected drift.

## Operational Standards

- **Complete templates:** Define encryption, Block Public Access, versioning, lifecycle, and logging in every bucket template. Do not rely on post-deployment manual configuration.
- **Change sets:** Create and review a change set before every stack update. Treat unexpected replacements as blockers.
- **Stack policies:** Apply stack policies to production stacks to protect critical resources.
- **Parameters:** Use parameters for all environment-specific values. Avoid hardcoding environment-specific names or ARNs in templates.
- **Drift detection:** Schedule regular drift detection on production stacks. Review and remediate drift findings.
- **Nested stacks:** Use nested stacks for reusable components. Define output exports for cross-stack references rather than hardcoding resource names.
- **Validation:** Run template validation and security scanning in CI before merging CloudFormation changes.

## Key Takeaways

- CloudFormation bucket resources require explicit definition of encryption, Block Public Access, versioning, and lifecycle configuration — the resource type alone creates an incompletely configured bucket.
- Change set review before every stack update is the primary control for catching unintended replacements on production S3 resources.
- Stack policies on production stacks prevent unintended resource modifications or replacements during routine deployments.
- Drift detection must be scheduled and reviewed regularly; drift that goes undetected causes unexpected behavior during subsequent stack updates.
- Parameters and nested stacks enable reusable, environment-aware CloudFormation templates that can be deployed consistently across development, staging, and production.
