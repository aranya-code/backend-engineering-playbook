# 07 - Automation & Scripting

## Overview

One of the biggest advantages of the AWS CLI is that it can be integrated into automation workflows. Instead of manually performing repetitive DynamoDB operations through the AWS Console, engineers can automate them using shell scripts, PowerShell, CI/CD pipelines, scheduled jobs, and Infrastructure as Code (IaC).

Production teams commonly automate:

- Health checks
- Table creation
- Backup creation
- Restore validation
- Data migration
- Cleanup jobs
- Deployment verification
- Disaster recovery

Automation reduces human error, improves consistency, and enables repeatable deployments.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Shell scripting with AWS CLI
- PowerShell automation
- JSON-driven commands
- Environment variables
- Batch execution
- Scheduled jobs
- CI/CD integration
- Automation best practices
- Production workflows

---

# Why Automate?

Manual operations:

```text
Engineer

↓

Open Console

↓

Navigate

↓

Click Buttons

↓

Repeat
```

Automated operations:

```text
Script

↓

AWS CLI

↓

DynamoDB

↓

Completed
```

Automation is:

- Faster
- Repeatable
- Version controlled
- Less error-prone

---

# Automation Architecture

```text
Developer

      │

      ▼

Git Repository

      │

      ▼

Shell Script

      │

      ▼

AWS CLI

      │

      ▼

Amazon DynamoDB
```

---

# Using Variables

Instead of hardcoding values:

```bash
TABLE_NAME="Orders"

aws dynamodb describe-table \
    --table-name "$TABLE_NAME"
```

Benefits:

- Reusable
- Easier maintenance
- Environment independent

---

# Using Environment Variables

Example:

```bash
export AWS_PROFILE=production

export AWS_REGION=us-east-1
```

Now commands become:

```bash
aws dynamodb list-tables
```

without repeatedly specifying:

```text
--profile

--region
```

---

# Reusable Shell Script

Example:

```bash
#!/bin/bash

TABLE_NAME="Orders"

aws dynamodb describe-table \
    --table-name "$TABLE_NAME"
```

Execute:

```bash
chmod +x health-check.sh

./health-check.sh
```

---

# Checking Multiple Tables

```bash
TABLES=("Orders" "Customers" "Products")

for table in "${TABLES[@]}"
do
    aws dynamodb describe-table \
        --table-name "$table"
done
```

Execution:

```text
Orders

↓

Customers

↓

Products
```

---

# Creating Backups for Multiple Tables

```bash
TABLES=("Orders" "Customers")

for table in "${TABLES[@]}"
do
    aws dynamodb create-backup \
        --table-name "$table" \
        --backup-name "${table}-$(date +%F)"
done
```

Useful before:

- Deployments
- Database migrations
- Maintenance windows

---

# Health Check Script

Verify table status.

```bash
STATUS=$(aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus" \
    --output text)

echo "$STATUS"
```

Expected output:

```text
ACTIVE
```

---

# Conditional Automation

Example:

```bash
if [ "$STATUS" = "ACTIVE" ]; then
    echo "Deployment can continue."
else
    echo "Table not ready."
fi
```

---

# Waiting for Resources

Instead of polling manually:

```bash
aws dynamodb wait table-exists \
    --table-name Orders
```

Automation flow:

```text
Create Table

↓

Wait

↓

Deploy
```

---

# Reading Commands from JSON

Example:

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item file://order.json
```

Advantages:

- Easier maintenance
- Version control
- Cleaner scripts

---

# Batch Automation

Example:

```bash
for file in data/*.json
do
    aws dynamodb put-item \
        --table-name Orders \
        --item file://"$file"
done
```

Useful for:

- Test data
- Seed data
- Migrations

---

# Exporting Table Metadata

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --output json \
    > table.json
```

Useful for:

- Documentation
- Auditing
- Environment comparison

---

# Using JMESPath in Scripts

Retrieve only the table status.

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus" \
    --output text
```

Instead of parsing large JSON documents.

---

# GitHub Actions Example

```yaml
name: Verify DynamoDB

on:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4

      - name: Verify Table
        run: |
          aws dynamodb describe-table \
            --table-name Orders
```

Typical pipeline:

```text
Git Push

↓

GitHub Actions

↓

AWS CLI

↓

Verify Infrastructure
```

---

# Cron Job Example

Nightly backup.

```bash
0 2 * * *

aws dynamodb create-backup \
    --table-name Orders \
    --backup-name Orders-$(date +\%F)
```

Runs every night at 2:00 AM.

---

# Deployment Validation

Typical workflow:

```text
Deploy

↓

Verify Table

↓

Verify TTL

↓

Verify Streams

↓

Verify PITR

↓

Application Ready
```

---

# Error Handling

Example:

```bash
aws dynamodb describe-table \
    --table-name Orders

if [ $? -ne 0 ]; then
    echo "Table verification failed."
    exit 1
fi
```

Automation should always validate exit codes.

---

# Logging Automation

Example:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    >> deploy.log
```

Useful for:

- Auditing
- Debugging
- CI/CD logs

---

# PowerShell Example

```powershell
$table = "Orders"

aws dynamodb describe-table `
    --table-name $table
```

Useful for Windows-based automation.

---

# Deployment Workflow

```text
Infrastructure

↓

Create Table

↓

Wait

↓

Enable TTL

↓

Enable Streams

↓

Enable PITR

↓

Run Smoke Tests

↓

Deploy Application
```

---

# Disaster Recovery Automation

```text
Failure

↓

Create Restore

↓

Wait

↓

Validate

↓

Switch Traffic
```

Many organizations automate disaster recovery testing on a regular schedule.

---

# Production Architecture

```text
GitHub Actions

        │

        ▼

Deployment Script

        │

        ▼

AWS CLI

        │

        ▼

Amazon DynamoDB

        │

        ▼

CloudWatch Logs
```

---

# Performance Considerations

- Reuse variables instead of duplicating commands.
- Use `--query` to minimize parsing overhead.
- Prefer JSON files over inline JSON.
- Batch related operations where possible.
- Avoid running expensive scans in automation scripts.

---

# Security Best Practices

- Store AWS credentials securely using IAM Roles or CI/CD secrets.
- Never hardcode access keys in scripts.
- Use least-privilege IAM policies.
- Log administrative operations.
- Validate environment variables before executing destructive commands.

---

# Best Practices

- Keep scripts idempotent whenever possible.
- Store scripts in version control.
- Parameterize table names and regions.
- Validate command exit codes.
- Automate repetitive operational tasks.
- Document automation workflows.

---

# Common Mistakes

## Hardcoding Environment Details

Poor:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --region us-east-1 \
    --profile production
```

Better:

```bash
export AWS_PROFILE=production
export AWS_REGION=us-east-1
```

---

## Ignoring Exit Codes

Automation should stop when critical commands fail.

Always check:

```bash
$?
```

---

## Parsing Large JSON Responses

Instead of processing the full response, use:

```bash
--query
```

to retrieve only the required fields.

---

## Running Destructive Commands Without Validation

Before executing:

```bash
delete-table
```

verify:

- AWS profile
- Region
- Environment
- Table name

---

# Interview Notes

A common interview question is:

> **Why is the AWS CLI commonly used in CI/CD pipelines?**

The AWS CLI provides a consistent, scriptable interface for interacting with AWS services, making it ideal for automating infrastructure provisioning, deployment verification, backups, and operational tasks.

---

Another common question is:

> **Why should automation scripts use `aws dynamodb wait` commands?**

Because many DynamoDB operations are asynchronous. Waiting ensures resources reach the expected state before subsequent steps execute, reducing deployment failures.

---

Another common question is:

> **Why should scripts use environment variables instead of hardcoded values?**

Environment variables make scripts reusable across development, staging, and production environments while reducing duplication and configuration errors.

---

Another common question is:

> **Why is checking CLI exit codes important?**

Exit codes indicate whether a command succeeded or failed. Automation should stop or retry on failures to prevent inconsistent deployments or data corruption.

---

# Key Takeaways

- Automation is one of the primary strengths of the AWS CLI.
- Shell scripts, PowerShell, and CI/CD pipelines can automate DynamoDB administration, backups, health checks, and deployments.
- Parameterized scripts, environment variables, and JSON input files improve maintainability and portability.
- Robust automation includes error handling, logging, validation, and waiting for asynchronous operations to complete.
- Well-designed automation reduces operational risk and is a key skill for senior backend and DevOps engineers.