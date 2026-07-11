# AWS CLI Cheat Sheet & Interview Guide

> A practical quick-reference guide containing the most frequently used AWS CLI commands, interview questions, troubleshooting commands, and production tips for Backend Engineers, DevOps Engineers, Cloud Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall common AWS CLI commands.
- Navigate AWS CLI efficiently during daily work.
- Prepare for AWS and DevOps interviews.
- Troubleshoot common CLI issues.
- Build faster automation scripts.
- Follow production-ready operational workflows.

---

# Why a Cheat Sheet?

Even experienced AWS engineers don't memorize every AWS CLI command.

Instead, they remember:

- Command structure
- Common patterns
- Frequently used options
- Troubleshooting workflow

Everything else is quickly referenced.

This chapter is designed to be that reference.

---

# General AWS CLI Syntax

Almost every command follows the same structure.

```bash
aws <service> <operation> [parameters] [global-options]
```

Example:

```bash
aws ec2 describe-instances \
--region ap-south-1 \
--profile production
```

---

# The Four Commands Every Engineer Uses Daily

## Check AWS CLI Version

```bash
aws --version
```

---

## Verify Current Identity

```bash
aws sts get-caller-identity
```

Always execute this before making production changes.

---

## View Current Configuration

```bash
aws configure list
```

Displays:

- Active profile
- Credentials
- Region
- Output format

---

## List Named Profiles

```bash
aws configure list-profiles
```

Useful when working with multiple AWS accounts.

---

# Frequently Used Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Select AWS account |
| `--region` | Override Region |
| `--output` | Output format |
| `--query` | Filter JSON |
| `--debug` | Debug requests |
| `--no-cli-pager` | Disable pager |
| `--cli-auto-prompt` | Interactive CLI |
| `--endpoint-url` | Custom endpoint |

These options work with almost every AWS CLI command.

---

# Most Common Output Formats

```bash
--output json
```

Recommended for automation.

---

```bash
--output table
```

Recommended for humans.

---

```bash
--output text
```

Recommended for shell scripting.

---

```bash
--output yaml
```

Useful for configuration-oriented workflows.

---

# Most Useful Authentication Commands

Configure CLI

```bash
aws configure
```

---

Configure Named Profile

```bash
aws configure \
--profile development
```

---

Login with AWS IAM Identity Center

```bash
aws sso login
```

---

Verify Active Identity

```bash
aws sts get-caller-identity
```

---

# Most Useful Troubleshooting Commands

Check configuration

```bash
aws configure list
```

---

Check Region

```bash
aws configure get region
```

---

Check version

```bash
aws --version
```

---

Enable debugging

```bash
aws s3 ls \
--debug
```

---

List profiles

```bash
aws configure list-profiles
```

---

# Most Useful JMESPath Examples

Retrieve EC2 Instance IDs

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].InstanceId"
```

---

Retrieve Bucket Names

```bash
aws s3api list-buckets \
--query "Buckets[].Name"
```

---

Retrieve Lambda Functions

```bash
aws lambda list-functions \
--query "Functions[].FunctionName"
```

---

Count S3 Buckets

```bash
aws s3api list-buckets \
--query "length(Buckets)"
```

---

# Daily Engineer Workflow

A recommended sequence before making infrastructure changes:

```text
Check AWS CLI Version
        │
        ▼
Verify AWS Identity
        │
        ▼
Verify Active Profile
        │
        ▼
Verify Region
        │
        ▼
Run Read-Only Command
        │
        ▼
Execute Change
        │
        ▼
Verify Result
```

Following this workflow significantly reduces operational mistakes.

---

# Production Quick Tips

- Always verify the active AWS account.
- Never rely on the default Region.
- Use Named Profiles.
- Prefer IAM Roles over Access Keys.
- Enable MFA.
- Use `--query` to reduce unnecessary output.
- Use `--debug` only while troubleshooting.
- Never expose credentials in scripts or repositories.

---

# Architecture Note

AWS CLI is a thin client.

Every command follows the same lifecycle:

```text
Read Configuration
        │
        ▼
Read Credentials
        │
        ▼
Sign Request
        │
        ▼
Send HTTPS Request
        │
        ▼
Receive Response
        │
        ▼
Filter Output
        │
        ▼
Display Result
```

Understanding this lifecycle makes troubleshooting significantly easier.

---

# Interview Note

One of the most common interview questions is:

> **What commands do you execute first when beginning work in a new AWS environment?**

A strong answer is:

1. Verify the AWS CLI version.
2. Verify the active identity using `aws sts get-caller-identity`.
3. Verify the active Region.
4. Verify the active profile.
5. Use read-only commands before making changes.

This demonstrates a disciplined and production-focused approach.


# AWS CLI Interview Questions & Answers

This section contains commonly asked AWS CLI interview questions ranging from beginner to senior backend engineer level.

Rather than memorizing commands, focus on understanding the reasoning behind each answer.

---

# Beginner Level

## 1. What is AWS CLI?

**Answer**

AWS Command Line Interface (AWS CLI) is a command-line tool that allows users to manage AWS services using commands instead of the AWS Management Console.

It communicates directly with AWS APIs and supports nearly every AWS service.

---

## 2. Why use AWS CLI instead of the AWS Console?

**Answer**

AWS CLI provides several advantages:

- Automation
- Scripting
- Faster operations
- CI/CD integration
- Infrastructure management
- Bulk operations
- Repeatability

The AWS Console is useful for exploration, while AWS CLI is preferred for operational tasks.

---

## 3. What command verifies that AWS CLI is installed?

```bash
aws --version
```

---

## 4. How do you configure AWS CLI?

```bash
aws configure
```

---

## 5. Which files store AWS CLI configuration?

Linux/macOS

```
~/.aws/config
```

```
~/.aws/credentials
```

Windows

```
C:\Users\<username>\.aws\
```

---

## 6. What is the difference between config and credentials files?

**config**

Stores:

- Region
- Output format
- Profile settings

**credentials**

Stores:

- Access Key ID
- Secret Access Key

---

## 7. What command verifies your current AWS identity?

```bash
aws sts get-caller-identity
```

This should be one of the first commands executed before making production changes.

---

## 8. What is a Named Profile?

A Named Profile is a separate AWS CLI configuration containing its own credentials and settings.

Example:

```bash
aws s3 ls --profile production
```

---

## 9. What is the purpose of `--region`?

It overrides the configured AWS Region for a single command.

---

## 10. What is the purpose of `--profile`?

It tells AWS CLI which Named Profile to use for authentication.

---

# Intermediate Level

## 11. How does AWS CLI authenticate requests?

AWS CLI:

1. Reads credentials.
2. Generates an AWS Signature Version 4 (SigV4) signature.
3. Sends an HTTPS request.
4. AWS validates the signature.
5. IAM evaluates permissions.

---

## 12. Does AWS CLI send the Secret Access Key to AWS?

No.

The Secret Access Key never leaves the local machine.

It is used to generate a cryptographic signature locally.

---

## 13. What is the Credential Provider Chain?

It is the predefined order AWS CLI follows when searching for credentials.

Examples include:

- Command-line options
- Environment variables
- Named Profiles
- Credentials file
- IAM Roles
- IAM Identity Center (SSO)

The first valid credentials found are used.

---

## 14. What is the difference between authentication and authorization?

Authentication verifies **who** you are.

Authorization determines **what** you are allowed to do.

---

## 15. Why are IAM Roles preferred over IAM Users?

IAM Roles use temporary credentials generated by AWS STS.

Temporary credentials:

- Expire automatically
- Reduce security risk
- Eliminate long-term Access Keys

---

## 16. What command enables detailed debugging?

```bash
aws s3 ls --debug
```

---

## 17. What does `--query` do?

It filters AWS API responses using JMESPath before displaying them.

Example:

```bash
aws s3api list-buckets \
--query "Buckets[].Name"
```

---

## 18. Which output format is best for automation?

```
json
```

---

## 19. Which output format is best for shell scripting?

```
text
```

---

## 20. How do you list every configured profile?

```bash
aws configure list-profiles
```

---

# Senior Level

## 21. Your deployment suddenly returns `AccessDenied`. What would you check first?

A structured approach:

1. Verify identity.

```bash
aws sts get-caller-identity
```

2. Verify profile.

3. Verify Region.

4. Review IAM policies.

5. Retry with:

```bash
--debug
```

Avoid changing permissions before identifying the active identity.

---

## 22. How would you troubleshoot "Unable to locate credentials"?

Steps:

- Check:

```bash
aws configure list
```

- Verify profile.

- Check environment variables.

- Login again if using SSO.

- Verify Credential Provider Chain.

---

## 23. How do you safely automate AWS CLI in CI/CD?

Recommended approach:

- IAM Roles
- GitHub OIDC
- Temporary credentials
- Least Privilege
- Logging
- Explicit Regions
- No hardcoded secrets

---

## 24. Why should production scripts specify `--region` explicitly?

It prevents accidental deployments to the wrong Region.

Never rely on default configuration inside automation.

---

## 25. Why should you verify identity before production changes?

Using:

```bash
aws sts get-caller-identity
```

confirms:

- AWS Account
- IAM User or Role
- Profile

This reduces accidental production mistakes.

---

## 26. Explain the difference between IAM Roles and STS.

IAM Role:

Defines permissions.

STS:

Generates temporary credentials after a role is assumed.

---

## 27. Why are temporary credentials safer?

Because they:

- Expire automatically
- Cannot be used indefinitely
- Reduce the impact of credential leakage

---

## 28. How would you debug a Region mismatch?

Verify:

```bash
aws configure get region
```

Override:

```bash
--region us-east-1
```

Then verify resources again.

---

## 29. Which AWS CLI commands do you use almost every day?

Typical answer:

```bash
aws sts get-caller-identity

aws configure list

aws s3 ls

aws ec2 describe-instances
```

along with:

```
--profile

--region

--query

--output json
```

---

## 30. What habits distinguish experienced AWS CLI users?

A strong answer would include:

- Verify identity before making changes.
- Prefer IAM Roles over IAM Users.
- Use Named Profiles.
- Avoid the Root account.
- Use `--query` for automation.
- Log automation.
- Validate infrastructure before deployment.
- Troubleshoot methodically instead of guessing.

---

# Quick Interview Tips

When answering AWS CLI interview questions:

- Explain **why**, not just **how**.
- Mention production best practices.
- Discuss security implications.
- Reference IAM Roles and temporary credentials.
- Demonstrate systematic troubleshooting.
- Use real examples from deployments or automation whenever possible.

---

# Interview Cheat Sheet

| Topic | Key Point |
|--------|-----------|
| Authentication | SigV4 signs requests locally |
| Authorization | IAM policies determine permissions |
| Identity | `aws sts get-caller-identity` |
| Configuration | `aws configure list` |
| Profiles | `aws configure list-profiles` |
| Debugging | `--debug` |
| Filtering | `--query` |
| Automation | `--output json` |
| Security | Prefer IAM Roles and temporary credentials |
| Troubleshooting | Verify Identity → Region → Permissions → Debug |


# Production Runbooks & Real-World Scenarios

This section contains real-world AWS CLI operational workflows that Backend Engineers, DevOps Engineers, and Cloud Engineers commonly perform in production.

Rather than memorizing commands, focus on following a repeatable workflow.

---

# Scenario 1 – Verify Your Environment Before Any Production Change

Before touching production resources, verify:

- AWS CLI version
- Active AWS account
- IAM identity
- Region
- Profile

Commands:

```bash
aws --version

aws sts get-caller-identity

aws configure list

aws configure get region
```

Expected Outcome

You know exactly:

- Which AWS account you're using
- Which IAM identity is active
- Which Region is selected
- Which profile is being used

Never skip this step.

---

# Scenario 2 – Deployment Fails with AccessDenied

Error

```text
AccessDenied
```

Workflow

```
Check Identity

↓

Check Profile

↓

Check Region

↓

Review IAM Policy

↓

Retry with --debug
```

Commands

```bash
aws sts get-caller-identity

aws configure list

aws configure get region

aws s3 sync build/ s3://frontend \
--debug
```

Never immediately grant AdministratorAccess.

Find the actual missing permission.

---

# Scenario 3 – "Unable to Locate Credentials"

Workflow

```
Check Config

↓

Check Profile

↓

Check Environment Variables

↓

Login Again

↓

Retry
```

Commands

```bash
aws configure list

aws configure list-profiles

aws sso login

aws sts get-caller-identity
```

---

# Scenario 4 – Wrong AWS Account

Symptoms

Resources appear to be missing.

Example

```
No EC2 Instances

No S3 Bucket

No Lambda Functions
```

Reality

You're connected to another AWS account.

Always verify:

```bash
aws sts get-caller-identity
```

---

# Scenario 5 – Wrong Region

Symptoms

```
Resource Not Found

Empty Result
```

Verify

```bash
aws configure get region
```

Override

```bash
aws ec2 describe-instances \
--region us-east-1
```

Region mismatches are one of the most common AWS CLI issues.

---

# Scenario 6 – Deploying a CloudFormation Stack

Recommended Workflow

```
Validate Template

↓

Review Parameters

↓

Deploy

↓

Monitor

↓

Verify Resources
```

Commands

```bash
aws cloudformation validate-template \
--template-body file://template.yaml

aws cloudformation deploy \
--template-file template.yaml
```

Always validate before deploying.

---

# Scenario 7 – Upload Build Artifacts

Workflow

```
Build

↓

Verify Bucket

↓

Upload

↓

Verify Upload
```

Commands

```bash
aws s3 ls

aws s3 sync build/ s3://frontend-assets

aws s3 ls s3://frontend-assets
```

---

# Scenario 8 – Investigating an EC2 Issue

Workflow

```
Identify Instance

↓

Describe Instance

↓

Review Status

↓

Check Tags

↓

Investigate
```

Commands

```bash
aws ec2 describe-instances

aws ec2 describe-instance-status
```

Gather information before making changes.

---

# Scenario 9 – Verify IAM Identity

Always know who AWS thinks you are.

```bash
aws sts get-caller-identity
```

Typical output

```json
{
  "Account":"123456789012",
  "Arn":"arn:aws:iam::123456789012:role/ProductionRole"
}
```

This command should become second nature.

---

# Scenario 10 – Safe Automation

Checklist

```
✔ Explicit Profile

✔ Explicit Region

✔ Logging

✔ Error Handling

✔ Exit Codes

✔ IAM Role

✔ No Hardcoded Credentials
```

Example

```bash
aws s3 sync build/ s3://frontend \
--profile production \
--region ap-south-1
```

---

# Daily AWS CLI Workflow

```text
Open Terminal
      │
      ▼
aws --version
      │
      ▼
aws sts get-caller-identity
      │
      ▼
aws configure list
      │
      ▼
Verify Region
      │
      ▼
Run Read-Only Commands
      │
      ▼
Execute Changes
      │
      ▼
Verify Result
```

---

# Production Deployment Workflow

```text
Code Ready
      │
      ▼
Validate
      │
      ▼
Verify Identity
      │
      ▼
Verify Region
      │
      ▼
Deploy
      │
      ▼
Monitor
      │
      ▼
Verify
      │
      ▼
Document
```

---

# Incident Response Workflow

```text
Alert Received
      │
      ▼
Identify AWS Account
      │
      ▼
Identify Region
      │
      ▼
Identify Resource
      │
      ▼
Collect Evidence
      │
      ▼
Investigate
      │
      ▼
Fix
      │
      ▼
Verify
      │
      ▼
Document
```

---

# Senior Engineer Checklist

Experienced engineers typically:

- Verify identity before every production change.
- Prefer IAM Roles over IAM Users.
- Use Named Profiles.
- Avoid long-term Access Keys.
- Specify Regions explicitly.
- Use `--query` to reduce unnecessary output.
- Validate infrastructure before deployment.
- Log automation.
- Review destructive commands carefully.
- Troubleshoot systematically instead of guessing.

---

# Top 20 AWS CLI Commands

| Command | Purpose |
|----------|----------|
| `aws --version` | CLI version |
| `aws configure` | Configure CLI |
| `aws configure list` | View configuration |
| `aws configure list-profiles` | List profiles |
| `aws sts get-caller-identity` | Verify identity |
| `aws s3 ls` | List buckets |
| `aws s3 cp` | Copy objects |
| `aws s3 sync` | Synchronize directories |
| `aws ec2 describe-instances` | List EC2 instances |
| `aws ec2 stop-instances` | Stop EC2 instances |
| `aws ec2 start-instances` | Start EC2 instances |
| `aws ec2 terminate-instances` | Terminate instances |
| `aws iam list-users` | List IAM users |
| `aws lambda list-functions` | List Lambda functions |
| `aws cloudformation validate-template` | Validate templates |
| `aws cloudformation deploy` | Deploy stacks |
| `aws logs tail` | View CloudWatch logs |
| `aws ecs list-clusters` | List ECS clusters |
| `aws ecr describe-repositories` | List ECR repositories |
| `aws route53 list-hosted-zones` | List Route 53 hosted zones |

---

# AWS CLI Golden Rules

1. Never use the Root account.
2. Prefer IAM Roles over IAM Users.
3. Verify your identity before making changes.
4. Specify Regions explicitly.
5. Use Named Profiles.
6. Enable MFA.
7. Rotate credentials regularly.
8. Never hardcode secrets.
9. Log automation.
10. Validate before deploying.
11. Use Least Privilege.
12. Automate repetitive tasks.
13. Test in non-production first.
14. Review destructive commands twice.
15. Document operational procedures.

---

# Final Thoughts

AWS CLI is much more than a command-line tool.

Used effectively, it becomes the foundation for:

- Infrastructure Automation
- DevOps Workflows
- CI/CD Pipelines
- Cloud Operations
- Incident Response
- Production Troubleshooting
- Infrastructure as Code

Mastering AWS CLI is one of the highest-leverage skills for Backend Engineers, DevOps Engineers, Platform Engineers, Cloud Engineers, and AWS Solutions Architects.

---

