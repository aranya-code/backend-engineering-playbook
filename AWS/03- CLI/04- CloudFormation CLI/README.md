# README

## Overview

This folder contains the AWS CloudFormation CLI reference for creating, validating, deploying, inspecting, updating, troubleshooting, and recovering CloudFormation stacks.

The documentation is organized as a practical command-oriented workflow, progressing from basic CLI operations to production deployment safety, drift detection, StackSets, nested stacks, diagnostics, and recovery.

## Quick Navigation

| Document | Focus |
|---|---|
| [01- CloudFormation CLI Introduction.md](./01-%20CloudFormation%20CLI%20Introduction.md) | CloudFormation CLI fundamentals, prerequisites, authentication, profiles, and core command structure |
| [02- Template Validation and Inspection.md](./02-%20Template%20Validation%20and%20Inspection.md) | Template validation, inspection, summaries, and pre-deployment checks |
| [03- Stack Creation and Updates.md](./03-%20Stack%20Creation%20and%20Updates.md) | Creating stacks, updating infrastructure, parameters, capabilities, roles, and deployment workflows |
| [04- Stack Deletion and Lifecycle Commands.md](./04-%20Stack%20Deletion%20and%20Lifecycle%20Commands.md) | Stack deletion, lifecycle states, termination protection, and lifecycle management |
| [05- Parameters and Outputs.md](./05-%20Parameters%20and%20Outputs.md) | Stack parameters, outputs, parameter overrides, and cross-stack integration |
| [06- Change Sets.md](./06-%20Change%20Sets.md) | Previewing infrastructure changes, reviewing replacements, and controlled deployments |
| [07- Drift Detection.md](./07-%20Drift%20Detection.md) | Detecting configuration drift between CloudFormation and deployed resources |
| [08- StackSets.md](./08-%20StackSets.md) | Multi-account and multi-region infrastructure deployment with StackSets |
| [09- Nested Stacks.md](./09-%20Nested%20Stacks.md) | Managing modular CloudFormation architectures with nested stacks |
| [10- Stack Events and Diagnostics.md](./10-%20Stack%20Events%20and%20Diagnostics.md) | Stack events, failure diagnosis, resource inspection, and troubleshooting workflows |
| [11- Rollback and Recovery Commands.md](./11-%20Rollback%20and%20Recovery%20Commands.md) | Rollback failures, recovery workflows, and `continue-update-rollback` |
| [12- CloudFormation CLI Cheat Sheet.md](./12-%20CloudFormation%20CLI%20Cheat%20Sheet.md) | High-value CloudFormation CLI commands and production deployment reference |

## Recommended Reading Order

```text
CloudFormation CLI Introduction
            |
            v
Template Validation and Inspection
            |
            v
Stack Creation and Updates
            |
            v
Stack Deletion and Lifecycle Commands
            |
            v
Parameters and Outputs
            |
            v
Change Sets
            |
            v
Drift Detection
            |
            +-------------------+
            |                   |
            v                   v
       Nested Stacks         StackSets
            |
            v
Stack Events and Diagnostics
            |
            v
Rollback and Recovery Commands
            |
            v
CloudFormation CLI Cheat Sheet
```

## Core Workflow

A production CloudFormation workflow should generally follow:

```text
Write Template
     |
     v
Validate Template
     |
     v
Inspect Template
     |
     v
Create / Update Change Set
     |
     v
Review Resource Changes
     |
     v
Execute Change Set
     |
     v
Monitor Stack Events
     |
     v
Verify Stack Status
     |
     v
Verify Resources and Outputs
```

For failed deployments:

```text
Deployment Failure
       |
       v
Check Stack Status
       |
       v
Inspect Stack Events
       |
       v
Identify Failed Resource
       |
       v
Inspect AWS Service Error
       |
       v
Fix Root Cause
       |
       v
Recover / Retry
```

## Production Command Categories

| Category | Primary Commands |
|---|---|
| Identity | `aws sts get-caller-identity` |
| Validation | `validate-template` |
| Stack inspection | `describe-stacks`, `list-stacks` |
| Resource inspection | `list-stack-resources` |
| Deployment | `create-stack`, `update-stack` |
| Change review | `create-change-set`, `describe-change-set` |
| Change execution | `execute-change-set` |
| Diagnostics | `describe-stack-events` |
| Recovery | `continue-update-rollback` |
| Deletion | `delete-stack` |
| Protection | `update-termination-protection` |
| Drift | `detect-stack-drift`, `describe-stack-resource-drifts` |
| Templates | `get-template`, `get-template-summary` |
| Dependencies | `list-exports` |
| Multi-account deployment | StackSet commands |
| Automation | CloudFormation waiters |

## Production Deployment Principles

- Verify the AWS account and region before making changes.
- Validate templates before deployment.
- Prefer change sets for important production updates.
- Review resource replacement carefully.
- Protect critical stacks with termination protection.
- Use least-privilege CloudFormation execution roles.
- Keep secrets out of templates, shell history, and CI/CD logs.
- Monitor stack events during deployments.
- Treat `UPDATE_ROLLBACK_FAILED` as a recovery state requiring investigation.
- Do not use `--resources-to-skip` without understanding the resulting infrastructure state.
- Use drift detection when manual changes or configuration divergence are suspected.
- Keep CloudFormation templates version-controlled.
- Use CI/CD for repeatable infrastructure deployment rather than unmanaged manual changes.
- Verify both CloudFormation state and the resulting AWS resources after deployment.

## Key Takeaways

- This folder is the operational CLI reference for AWS CloudFormation.
- The documents progress from basic CLI usage to production deployment and recovery workflows.
- **Validation → Change Set → Review → Execute → Monitor → Verify** is the preferred production deployment pattern.
- **Stack Events** are the primary diagnostic source when a deployment fails.
- **Change Sets** provide visibility into potentially destructive updates before execution.
- **Drift Detection** identifies divergence between CloudFormation-managed configuration and actual resource configuration.
- **StackSets** support standardized infrastructure deployment across accounts and regions.
- **Nested Stacks** provide modularity for larger CloudFormation architectures.
- **Rollback and recovery commands** are critical when a stack becomes stuck during an update or rollback.
- The **CloudFormation CLI Cheat Sheet** serves as the final quick-reference document for day-to-day operations.