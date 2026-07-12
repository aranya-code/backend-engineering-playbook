# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used AWS CloudFormation CLI commands, Infrastructure as Code (IaC) workflows, troubleshooting techniques, and interview preparation. This chapter serves as a daily operational guide for Backend Engineers, DevOps Engineers, Platform Engineers, Cloud Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used CloudFormation CLI commands
- Deploy infrastructure using CloudFormation
- Manage CloudFormation stacks
- Troubleshoot deployment failures
- Follow production deployment workflows
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

CloudFormation is heavily used in production automation.

Engineers rarely memorize every command.

Instead, they remember:

- Deployment workflow
- Stack lifecycle
- Change management
- Troubleshooting process

This chapter provides a quick operational reference.

---

# Command Syntax

General syntax:

```bash
aws cloudformation <operation> [options]
```

Examples:

```bash
aws cloudformation create-stack
```

```bash
aws cloudformation update-stack
```

```bash
aws cloudformation delete-stack
```

---

# Stack Management Commands

## List Stacks

```bash
aws cloudformation list-stacks
```

---

## Describe a Stack

```bash
aws cloudformation describe-stacks \
--stack-name backend-production
```

---

## Create a Stack

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml
```

---

## Update a Stack

```bash
aws cloudformation update-stack \
--stack-name backend-production \
--template-body file://template.yaml
```

---

## Delete a Stack

```bash
aws cloudformation delete-stack \
--stack-name backend-production
```

---

## Wait for Stack Creation

```bash
aws cloudformation wait stack-create-complete \
--stack-name backend-production
```

---

## Wait for Stack Update

```bash
aws cloudformation wait stack-update-complete \
--stack-name backend-production
```

---

## Wait for Stack Deletion

```bash
aws cloudformation wait stack-delete-complete \
--stack-name backend-production
```

---

# Template Commands

## Validate Template

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

---

## Create Stack with Parameters

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml \
--parameters \
ParameterKey=Environment,ParameterValue=Production
```

---

## Create Stack with IAM Resources

```bash
aws cloudformation create-stack \
--stack-name backend-production \
--template-body file://template.yaml \
--capabilities CAPABILITY_NAMED_IAM
```

---

# Stack Resource Commands

## List Stack Resources

```bash
aws cloudformation list-stack-resources \
--stack-name backend-production
```

---

## Describe Stack Events

```bash
aws cloudformation describe-stack-events \
--stack-name backend-production
```

---

## Get Template

```bash
aws cloudformation get-template \
--stack-name backend-production
```

---

# Change Set Commands

## Create Change Set

```bash
aws cloudformation create-change-set
```

---

## List Change Sets

```bash
aws cloudformation list-change-sets
```

---

## Describe Change Set

```bash
aws cloudformation describe-change-set
```

---

## Execute Change Set

```bash
aws cloudformation execute-change-set
```

---

## Delete Change Set

```bash
aws cloudformation delete-change-set
```

---

# Drift Detection Commands

## Detect Drift

```bash
aws cloudformation detect-stack-drift
```

---

## Drift Detection Status

```bash
aws cloudformation describe-stack-drift-detection-status
```

---

## Describe Resource Drift

```bash
aws cloudformation describe-stack-resource-drifts
```

---

# StackSet Commands

## Create StackSet

```bash
aws cloudformation create-stack-set
```

---

## List StackSets

```bash
aws cloudformation list-stack-sets
```

---

## Describe StackSet

```bash
aws cloudformation describe-stack-set
```

---

## Create Stack Instances

```bash
aws cloudformation create-stack-instances
```

---

## List Stack Instances

```bash
aws cloudformation list-stack-instances
```

---

## Delete StackSet

```bash
aws cloudformation delete-stack-set
```

---

# Export & Import Commands

## List Exports

```bash
aws cloudformation list-exports
```

---

## List Imports

```bash
aws cloudformation list-imports
```

---

# Rollback Commands

## Continue Rollback

```bash
aws cloudformation continue-update-rollback
```

---

## Cancel Update

```bash
aws cloudformation cancel-update-stack
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable verbose logging |
| `--no-cli-pager` | Disable CLI pager |

---

# Common Stack Statuses

| Status | Meaning |
|---------|---------|
| `CREATE_IN_PROGRESS` | Stack is being created |
| `CREATE_COMPLETE` | Stack created successfully |
| `UPDATE_IN_PROGRESS` | Stack update started |
| `UPDATE_COMPLETE` | Stack updated successfully |
| `UPDATE_ROLLBACK_IN_PROGRESS` | Rolling back failed update |
| `UPDATE_ROLLBACK_COMPLETE` | Rollback completed |
| `DELETE_IN_PROGRESS` | Stack deletion started |
| `DELETE_COMPLETE` | Stack deleted |
| `CREATE_FAILED` | Stack creation failed |
| `DELETE_FAILED` | Stack deletion failed |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| ValidationError | Invalid template or stack | Validate template or verify stack name |
| CREATE_FAILED | Resource creation failed | Review stack events |
| UPDATE_ROLLBACK_FAILED | Rollback failed | Continue rollback after resolving the issue |
| DELETE_FAILED | Resource dependency | Remove dependencies before deleting |
| AlreadyExistsException | Duplicate resource | Use a unique resource name |
| InsufficientCapabilitiesException | IAM resources in template | Use `CAPABILITY_NAMED_IAM` |
| No updates are to be performed | No infrastructure changes | Informational message |

---

# CloudFormation Deployment Workflow

```text
Write Template
      │
      ▼
Validate Template
      │
      ▼
Commit to Git
      │
      ▼
CI/CD Pipeline
      │
      ▼
Create Change Set
      │
      ▼
Review Changes
      │
      ▼
Execute Change Set
      │
      ▼
Monitor Stack Events
      │
      ▼
Deployment Complete
```

---

# Daily CloudFormation Checklist

Before every deployment:

- Verify AWS account.
- Verify Region.
- Validate the template.
- Review parameters.
- Create a Change Set.
- Review replacement operations.
- Verify IAM permissions.
- Monitor stack events.
- Run drift detection periodically.

---

# Interview Questions

## 1. What is CloudFormation?

**Answer**

CloudFormation is AWS's Infrastructure as Code (IaC) service that provisions and manages AWS resources using YAML or JSON templates.

---

## 2. What is a Stack?

**Answer**

A Stack is a collection of AWS resources created and managed together from a CloudFormation template.

---

## 3. What is the difference between a Template and a Stack?

**Answer**

A Template is the infrastructure blueprint, while a Stack is the deployed instance of that template.

---

## 4. Why are Change Sets important?

**Answer**

Change Sets preview infrastructure modifications before deployment, allowing engineers to review additions, deletions, replacements, and updates before applying them to production.

---

## 5. What is Drift Detection?

**Answer**

Drift Detection identifies differences between the CloudFormation template and the actual deployed infrastructure, helping detect manual changes made outside CloudFormation.

---

## 6. What is a StackSet?

**Answer**

A StackSet deploys the same CloudFormation stack across multiple AWS accounts and Regions, making it ideal for enterprise-scale infrastructure management.

---

## 7. Why are Nested Stacks useful?

**Answer**

Nested Stacks divide large templates into smaller reusable components, improving maintainability, scalability, and team collaboration.

---

## 8. What happens when a CloudFormation update fails?

**Answer**

CloudFormation automatically initiates a rollback to restore the infrastructure to its last stable state. If rollback fails, the stack enters the `UPDATE_ROLLBACK_FAILED` state and requires manual intervention.

---

## 9. Why should templates be stored in Git?

**Answer**

Version control provides history, collaboration, code review, rollback capability, and integration with CI/CD pipelines.

---

## 10. How would you troubleshoot a failed CloudFormation deployment?

**Answer**

I would validate the template, review stack events to identify the first failed resource, verify parameter values and IAM permissions, check for service quotas or resource conflicts, correct the issue, and redeploy or continue the rollback if required.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Write modular CloudFormation templates.
- Store templates in Git.
- Use YAML instead of JSON.
- Parameterize environment-specific values.
- Validate templates before deployment.
- Review Change Sets before production updates.
- Run Drift Detection regularly.
- Never modify CloudFormation-managed resources manually.
- Use StackSets for multi-account deployments.
- Automate deployments through CI/CD pipelines.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Stacks | `aws cloudformation list-stacks` |
| Create Stack | `aws cloudformation create-stack` |
| Update Stack | `aws cloudformation update-stack` |
| Delete Stack | `aws cloudformation delete-stack` |
| Validate Template | `aws cloudformation validate-template` |
| List Stack Resources | `aws cloudformation list-stack-resources` |
| Describe Stack Events | `aws cloudformation describe-stack-events` |
| Create Change Set | `aws cloudformation create-change-set` |
| Execute Change Set | `aws cloudformation execute-change-set` |
| Detect Drift | `aws cloudformation detect-stack-drift` |
| Create StackSet | `aws cloudformation create-stack-set` |
| List Exports | `aws cloudformation list-exports` |

---

# Final Thoughts

AWS CloudFormation is the foundation of Infrastructure as Code on AWS. Mastering the CloudFormation CLI enables you to provision, update, and manage cloud infrastructure in a repeatable, auditable, and automated manner. Combined with Git, CI/CD, Change Sets, StackSets, and Drift Detection, CloudFormation provides a powerful framework for managing production infrastructure at any scale.

---
