# README

## Overview

This section contains a production-oriented troubleshooting reference for AWS CloudFormation failures.

The documentation focuses on diagnosing failures systematically across the CloudFormation lifecycle, including:

- Template validation
- Stack creation
- Stack updates
- Rollbacks
- Stack deletion
- Change sets
- Drift detection
- StackSets
- Nested and cross-stack dependencies
- IAM authorization
- CloudFormation capabilities

The goal is to troubleshoot from **CloudFormation event → failing resource → underlying AWS API → authorization/configuration/dependency issue**, rather than treating the CloudFormation error message as the root cause.

## Troubleshooting Approach

Use the following workflow for most CloudFormation incidents:

```text
CloudFormation Failure
        |
        v
Identify Stack / Operation
        |
        v
Inspect CloudFormation Events
        |
        v
Identify Failed Resource
        |
        v
Determine Failure Category
        |
        +------------------+
        |        |         |
        v        v         v
     Template  IAM      Resource
     / Config  / Auth   / Dependency
        |        |         |
        +--------+---------+
                 |
                 v
        Inspect Underlying
          AWS API Failure
                 |
                 v
        Correct Root Cause
                 |
                 v
        Retry / Recover
```

Start with:

```bash
aws sts get-caller-identity

aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region <region>
```

For failed resources, focus on:

- `LogicalResourceId`
- `ResourceType`
- `ResourceStatus`
- `ResourceStatusReason`
- Previous resource state
- Related dependencies
- CloudFormation execution role
- Underlying AWS service events

## Quick Navigation

| Document | Focus |
|---|---|
| [01- Troubleshooting Methodology](./01-%20Troubleshooting%20Methodology.md) | Systematic CloudFormation troubleshooting workflow |
| [02- Template Validation Errors](./02-%20Template%20Validation%20Errors.md) | YAML/JSON, intrinsic functions, schema, syntax, and template validation failures |
| [03- Stack Creation Failures](./03-%20Stack%20Creation%20Failures.md) | Resource provisioning and initial stack creation failures |
| [04- Stack Update and Rollback Failures](./04-%20Stack%20Update%20and%20Rollback%20Failures.md) | Update failures, rollback states, and recovery |
| [05- Stack Deletion Failures](./05-%20Stack%20Deletion%20Failures.md) | Resource deletion failures and stuck stacks |
| [06- Change Set Failures](./06-%20Change%20Set%20Failures.md) | Change set creation, validation, and execution failures |
| [07- Drift Detection Failures](./07-%20Drift%20Detection%20Failures.md) | Drift detection and unexpected resource state issues |
| [08- StackSet Operation Failures](./08-%20StackSet%20Operation%20Failures.md) | Multi-account and multi-Region StackSet failures |
| [09- Nested Stack and Cross Stack Issues](./09-%20Nested%20Stack%20and%20Cross%20Stack%20Issues.md) | Nested stacks, exports, imports, and stack dependencies |
| [10- IAM and Capability Errors](./10-%20IAM%20and%20Capability%20Errors.md) | IAM authorization, capabilities, execution roles, and `iam:PassRole` |

## Failure Categories

| Category | Typical Symptoms | Primary Investigation |
|---|---|---|
| Template validation | Invalid template, malformed YAML, unsupported property | Template validation |
| Stack creation | `CREATE_FAILED` | Stack events and resource API |
| Stack update | `UPDATE_FAILED` | Change and resource events |
| Rollback | `UPDATE_ROLLBACK_FAILED` | Failed rollback resource |
| Deletion | `DELETE_FAILED` | Resource dependencies and deletion protection |
| Change set | Change set fails or cannot execute | Change set status and reason |
| Drift | Unexpected resource configuration | Drift detection results |
| StackSet | Failed account/Region operations | StackSet operation status |
| Nested stack | Child stack failure | Parent and child stack events |
| Cross-stack | Export/import failures | `Exports`, `Imports`, dependencies |
| IAM | `AccessDenied` | Effective identity and authorization chain |
| Capabilities | `InsufficientCapabilities` | Required capability acknowledgement |

## Core Diagnostic Commands

### Identify the Current AWS Identity

```bash
aws sts get-caller-identity
```

### Describe a Stack

```bash
aws cloudformation describe-stacks \
  --stack-name <stack-name> \
  --region <region>
```

### Inspect Stack Events

```bash
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region <region>
```

### Show Failed Events

```bash
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region <region> \
  --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].{LogicalId:LogicalResourceId,Type:ResourceType,Status:ResourceStatus,Reason:ResourceStatusReason}'
```

### Validate a Template

```bash
aws cloudformation validate-template \
  --template-body file://template.yaml \
  --region <region>
```

### Inspect Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name <stack-name> \
  --region <region> \
  --query 'Stacks[0].{Name:StackName,Status:StackStatus,Reason:StackStatusReason,Role:RoleARN}'
```

### Inspect Change Sets

```bash
aws cloudformation list-change-sets \
  --stack-name <stack-name> \
  --region <region>
```

```bash
aws cloudformation describe-change-set \
  --stack-name <stack-name> \
  --change-set-name <change-set-name> \
  --region <region>
```

### Inspect Stack Exports

```bash
aws cloudformation list-exports \
  --region <region>
```

### Inspect Imported Values

```bash
aws cloudformation list-imports \
  --export-name <export-name> \
  --region <region>
```

## Event-First Troubleshooting

CloudFormation stack status usually provides only the high-level failure state.

For example:

```text
UPDATE_ROLLBACK_FAILED
```

is a condition, not necessarily the root cause.

The useful information is normally found in the resource event:

```text
LogicalResourceId
        |
        v
ResourceType
        |
        v
ResourceStatusReason
        |
        v
Underlying AWS Service Error
```

For example:

```text
AWS::IAM::Role
        |
        v
CREATE_FAILED
        |
        v
User is not authorized to perform iam:CreateRole
```

The troubleshooting target is therefore the underlying IAM authorization failure, not the generic CloudFormation stack state.

## Recovery Principle

Do not immediately delete and recreate a failed production stack.

First determine:

1. What operation failed?
2. Which resource failed?
3. Why did the resource operation fail?
4. Is the stack recoverable?
5. Did CloudFormation enter a rollback state?
6. Are dependencies preventing recovery?
7. Is the failure caused by configuration, permissions, or external resource state?
8. What state will the next operation leave behind?

A production recovery should preserve infrastructure state whenever possible and avoid destructive actions until the dependency chain is understood.

## IAM Authorization Chain

IAM failures should be investigated across the complete authorization path:

```text
CloudFormation
      |
      v
Execution Role
      |
      v
AWS API
      |
      v
Identity Policy
      |
      +---- Permission Boundary
      |
      +---- SCP
      |
      +---- Session Policy
      |
      v
Effective Authorization
```

Common failures include:

- Missing `cloudformation:*` permissions on the deployment identity.
- Missing resource permissions on the CloudFormation execution role.
- Missing `iam:PassRole`.
- Incorrect role trust policy.
- Permission boundary restrictions.
- Organization SCP restrictions.
- Explicit IAM resource name collisions.

See [10- IAM and Capability Errors](./10-%20IAM%20and%20Capability%20Errors.md) for the detailed IAM troubleshooting workflow.

## Production Troubleshooting Principles

### Inspect Before Modifying

Capture the current state before attempting recovery:

```bash
aws cloudformation describe-stacks \
  --stack-name <stack-name> \
  --region <region>

aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region <region>
```

### Treat the First Useful Error as Evidence

The final stack status may be a consequence of an earlier resource failure.

Prefer:

```text
ResourceStatusReason
```

over:

```text
StackStatus
```

when determining the root cause.

### Check External Changes

CloudFormation may fail because an AWS resource was modified outside CloudFormation.

Investigate:

- Manual console changes
- CLI changes
- Terraform or other IaC changes
- Resource deletion
- Resource replacement
- Changed IAM policies
- Changed networking configuration
- Changed security groups
- Changed dependencies

### Consider Dependencies

A resource may be healthy by itself but fail because another resource is unavailable, incorrectly configured, or being replaced.

Common dependency chains include:

```text
VPC
 |
 +--> Subnet
       |
       +--> Security Group
              |
              +--> Load Balancer
                     |
                     +--> ECS / EC2 / Lambda
```

### Avoid Blind Retries

Retrying without understanding the failure can:

- Reproduce the same failure.
- Trigger additional resource changes.
- Complicate rollback.
- Increase operational risk.
- Leave partially modified infrastructure.

Determine whether the failure is:

- Transient
- Configuration-related
- Authorization-related
- Dependency-related
- State-related
- Irreversible without manual intervention

## CI/CD Integration

CloudFormation troubleshooting should be integrated into the deployment pipeline rather than performed only after production failures.

A production pipeline should typically include:

```text
Commit
  |
  v
Template Validation
  |
  v
Lint / Static Analysis
  |
  v
IAM / Security Checks
  |
  v
Change Set
  |
  v
Review / Approval
  |
  v
Execute
  |
  v
Monitor Stack Events
  |
  v
Verify Resources
```

Useful deployment practices include:

- Validate templates before deployment.
- Use dedicated deployment roles.
- Use least-privilege execution roles.
- Use change sets for high-risk changes.
- Capture CloudFormation events in CI/CD logs.
- Fail pipelines when CloudFormation operations fail.
- Keep infrastructure changes version-controlled.
- Avoid manual production changes where possible.
- Record recovery actions for operational incidents.

## Security Considerations

CloudFormation troubleshooting often exposes privileged infrastructure operations.

Follow these practices:

- Use short-lived AWS credentials.
- Prefer role assumption over long-lived access keys.
- Restrict CloudFormation execution roles.
- Restrict `iam:PassRole`.
- Review IAM changes through code review.
- Avoid `AdministratorAccess` as a troubleshooting shortcut.
- Protect CloudFormation templates and deployment configuration.
- Avoid storing secrets directly in templates.
- Audit deployment activity through CloudTrail.
- Apply organizational controls such as SCPs and permission boundaries deliberately.

## Operational Checklist

Use this checklist during a CloudFormation incident:

- [ ] Confirm the AWS account.
- [ ] Confirm the AWS Region.
- [ ] Identify the deployment identity.
- [ ] Identify the CloudFormation execution role.
- [ ] Check the stack status.
- [ ] Inspect recent stack events.
- [ ] Identify the first meaningful resource failure.
- [ ] Identify the underlying AWS service error.
- [ ] Check resource dependencies.
- [ ] Check IAM permissions if authorization is involved.
- [ ] Check `iam:PassRole` when roles are passed to services.
- [ ] Check permission boundaries.
- [ ] Check SCPs when applicable.
- [ ] Check for resources modified outside CloudFormation.
- [ ] Check change set status for update operations.
- [ ] Check child stacks for nested stack failures.
- [ ] Check exports/imports for cross-stack failures.
- [ ] Check StackSet operation status for multi-account deployments.
- [ ] Determine whether rollback or recovery is safe.
- [ ] Capture the final root cause and remediation.

## Key Takeaways

- CloudFormation troubleshooting should be **event-first and resource-specific**.
- A stack status such as `UPDATE_ROLLBACK_FAILED` describes the current state but may not identify the original root cause.
- `ResourceStatusReason` is often the most valuable diagnostic field.
- Always verify the AWS account, Region, and deployment identity.
- Determine whether CloudFormation is operating under a dedicated execution role.
- Treat IAM capabilities, IAM permissions, SCPs, and permission boundaries as separate authorization concerns.
- Investigate resource dependencies before performing destructive recovery actions.
- Avoid blind retries and unnecessary stack deletion.
- Use change sets to make potentially destructive updates reviewable.
- Use CloudTrail when the underlying AWS API operation or principal is unclear.
- Nested stacks and StackSets require troubleshooting at both the orchestration and child-resource levels.
- Cross-stack failures commonly involve export/import dependencies and resource lifecycle constraints.
- Production troubleshooting should preserve infrastructure state whenever possible.
- CI/CD pipelines should validate, review, execute, and monitor CloudFormation deployments systematically.
- The objective is not merely to make the stack reach `CREATE_COMPLETE` or `UPDATE_COMPLETE`; it is to identify and correct the underlying infrastructure failure safely.