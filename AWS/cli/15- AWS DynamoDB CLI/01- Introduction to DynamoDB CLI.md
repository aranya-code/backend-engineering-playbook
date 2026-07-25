# 01 - Introduction to DynamoDB CLI

## Overview

The **AWS Command Line Interface (AWS CLI)** provides a powerful way to interact with Amazon DynamoDB directly from the terminal.

While many developers primarily use:

- AWS Console
- Boto3 SDK
- AWS SDKs

experienced backend engineers frequently rely on the CLI for:

- Debugging production issues
- Verifying table configurations
- Automating deployments
- Creating backup scripts
- CI/CD pipelines
- Infrastructure validation
- Rapid testing

The CLI exposes nearly every DynamoDB API and is an essential tool for DevOps, Backend, and Cloud Engineers.

---

# Learning Objectives

After completing this chapter, you'll understand:

- What the AWS CLI is
- Why engineers use it
- CLI architecture
- Authentication
- Command syntax
- Profiles
- Regions
- Output formats
- JMESPath filtering
- JSON input
- Debug mode
- Production best practices

---

# Why Use the CLI?

The AWS Console is excellent for exploration.

However, production engineers often need automation.

Instead of clicking:

```text
AWS Console

↓

Search Table

↓

Click Backup

↓

Click Restore
```

the CLI allows:

```bash
aws dynamodb create-backup \
    --table-name Orders \
    --backup-name Orders-Backup
```

Everything becomes scriptable.

---

# AWS CLI Architecture

```text
                User

                  │

                  ▼

            AWS CLI Command

                  │

                  ▼

          AWS Authentication

                  │

                  ▼

          DynamoDB API

                  │

                  ▼

         Amazon DynamoDB
```

The CLI sends signed HTTPS requests to the same DynamoDB APIs used by SDKs.

---

# CLI vs Console vs SDK

| Feature | Console | CLI | SDK |
|----------|----------|-----|-----|
| GUI | ✅ | ❌ | ❌ |
| Automation | ❌ | ✅ | ✅ |
| Scripting | ❌ | ✅ | ✅ |
| Programming | ❌ | ❌ | ✅ |
| CI/CD | ❌ | ✅ | ✅ |
| Production Debugging | Limited | Excellent | Excellent |

---

# Installing AWS CLI

Verify installation:

```bash
aws --version
```

Example output:

```text
aws-cli/2.31.0 Python/3.x Windows/Linux/macOS
```

---

# Configuring Credentials

Configure AWS credentials:

```bash
aws configure
```

Example:

```text
AWS Access Key ID:
AWS Secret Access Key:
Default region:
Default output format:
```

Configuration files are typically stored in:

```text
~/.aws/config

~/.aws/credentials
```

---

# Using IAM Roles

Production workloads should avoid static credentials.

Preferred authentication:

```text
EC2

↓

IAM Role

↓

Temporary Credentials

↓

DynamoDB
```

Also applicable to:

- Lambda
- ECS
- EKS

---

# Command Structure

Basic syntax:

```bash
aws <service> <operation> [parameters]
```

Example:

```bash
aws dynamodb list-tables
```

Breakdown:

```text
aws

↓

dynamodb

↓

list-tables
```

---

# Getting Help

View help:

```bash
aws help
```

Service help:

```bash
aws dynamodb help
```

Operation help:

```bash
aws dynamodb get-item help
```

The built-in documentation is extremely useful.

---

# Listing Tables

```bash
aws dynamodb list-tables
```

Example output:

```json
{
  "TableNames": [
    "Customers",
    "Orders",
    "Products"
  ]
}
```

---

# Describing a Table

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Returns:

- Key schema
- Billing mode
- Table status
- Item count
- Indexes
- Stream configuration

---

# Regions

Specify a region:

```bash
aws dynamodb list-tables \
    --region us-east-1
```

Or configure a default region:

```bash
aws configure
```

Avoid hardcoding regions in scripts whenever possible.

---

# AWS Profiles

Organizations often use multiple AWS accounts.

Example:

```bash
aws dynamodb list-tables \
    --profile production
```

Other examples:

```text
default

development

staging

production
```

Profiles simplify account switching.

---

# Output Formats

AWS CLI supports multiple output formats.

### JSON

```bash
--output json
```

Best for:

- APIs
- Automation
- Debugging

---

### Table

```bash
--output table
```

Example:

```text
------------------------
|      ListTables      |
+----------------------+
| Orders               |
| Customers            |
+----------------------+
```

Useful for humans.

---

### Text

```bash
--output text
```

Ideal for shell scripts.

---

### YAML

```bash
--output yaml
```

Helpful for configuration inspection.

---

# Global Options

Common options:

```bash
--profile

--region

--output

--query

--debug

--no-cli-pager
```

These work across most AWS CLI commands.

---

# JSON Input

Complex requests are easier to manage using JSON files.

Example:

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item file://order.json
```

Example `order.json`:

```json
{
  "order_id": {
    "S": "1001"
  },
  "status": {
    "S": "PAID"
  }
}
```

This keeps commands readable and reusable.

---

# JMESPath Queries

AWS CLI supports client-side filtering using JMESPath.

Example:

```bash
aws dynamodb list-tables \
    --query "TableNames"
```

Output:

```json
[
  "Orders",
  "Customers"
]
```

More advanced example:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus"
```

Output:

```text
ACTIVE
```

---

# Debug Mode

Enable request debugging:

```bash
aws dynamodb list-tables \
    --debug
```

Useful for:

- Authentication failures
- Signature errors
- Network issues
- API troubleshooting

---

# CLI Exit Codes

CLI commands return exit codes.

```text
0

↓

Success
```

```text
Non-zero

↓

Failure
```

This is useful in automation scripts.

Example:

```bash
if [ $? -eq 0 ]; then
    echo "Success"
fi
```

---

# CLI in CI/CD

Typical workflow:

```text
GitHub Actions

↓

AWS CLI

↓

Create Table

↓

Run Tests

↓

Delete Resources
```

The CLI integrates naturally into deployment pipelines.

---

# CLI vs Boto3

| Feature | CLI | Boto3 |
|----------|------|--------|
| Interactive | ✅ | ❌ |
| Automation Scripts | ✅ | ✅ |
| Python Applications | ❌ | ✅ |
| CI/CD | ✅ | ✅ |
| Debugging | Excellent | Excellent |
| Reusable Application Logic | ❌ | ✅ |

Use:

- CLI for administration and automation.
- Boto3 for application development.

---

# Common Production Uses

Senior engineers commonly use the CLI to:

- Verify table status
- Check indexes
- Enable backups
- Configure TTL
- Inspect Streams
- Export data
- Restore backups
- Troubleshoot IAM issues
- Validate deployments
- Execute maintenance scripts

---

# Production Architecture

```text
            Developer

                │

                ▼

            AWS CLI

                │

                ▼

        Signed HTTPS Request

                │

                ▼

         Amazon DynamoDB

                │

                ▼

      CloudWatch / CloudTrail
```

---

# Performance Considerations

- Use JSON files for large requests.
- Use `--query` to reduce unnecessary output.
- Disable pagination when appropriate using `--no-cli-pager`.
- Prefer scripting over repetitive manual operations.
- Avoid running large Scan operations from the CLI against production tables.

---

# Security Best Practices

- Prefer IAM Roles over long-lived access keys.
- Use named profiles for different environments.
- Never commit credentials to source control.
- Rotate access keys regularly if static credentials are unavoidable.
- Use least-privilege IAM permissions.
- Avoid running production commands from the wrong profile.

---

# Best Practices

- Learn the common DynamoDB commands.
- Use JSON input files for complex requests.
- Use JMESPath to filter output.
- Use named profiles instead of changing credentials.
- Validate commands in development before production.
- Integrate CLI commands into CI/CD pipelines.
- Keep frequently used commands in reusable scripts.

---

# Common Mistakes

## Running Commands Against the Wrong Account

Always verify:

```bash
--profile
```

before executing destructive operations.

---

## Hardcoding Credentials

Avoid embedding credentials directly in scripts.

Use:

- IAM Roles
- Named profiles
- Environment variables

---

## Ignoring Exit Codes

Automation scripts should always verify command success before continuing.

---

## Copy-Pasting Large JSON Inline

Poor:

```bash
aws dynamodb put-item --item '{ ... very large JSON ... }'
```

Better:

```bash
--item file://order.json
```

---

# Interview Notes

A common interview question is:

> **Why would you use the AWS CLI instead of Boto3?**

The AWS CLI is ideal for administration, debugging, scripting, and CI/CD automation. Boto3 is better suited for building Python applications and embedding DynamoDB operations into business logic.

---

Another common question is:

> **How do you switch between multiple AWS accounts?**

Use named AWS CLI profiles and specify the desired profile with the `--profile` option or configure the `AWS_PROFILE` environment variable.

---

Another common question is:

> **What is JMESPath in the AWS CLI?**

JMESPath is a query language that allows client-side filtering and transformation of JSON responses returned by AWS CLI commands.

---

Another common question is:

> **Why should production environments use IAM Roles instead of access keys?**

IAM Roles provide temporary credentials, reduce the risk of credential leakage, simplify credential rotation, and are the recommended authentication mechanism for AWS services.

---

# Key Takeaways

- The AWS CLI is an essential tool for managing, automating, and troubleshooting DynamoDB.
- Every CLI command maps directly to a DynamoDB API operation.
- Use named profiles, IAM Roles, and JMESPath to build secure and efficient workflows.
- JSON input files and reusable scripts improve maintainability and reduce errors.
- Mastering the CLI is a valuable skill for backend engineers, DevOps engineers, and cloud professionals working with AWS.