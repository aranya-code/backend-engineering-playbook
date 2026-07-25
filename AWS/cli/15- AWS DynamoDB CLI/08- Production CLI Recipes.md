# 08 - Production CLI Recipes

## Overview

Knowing individual AWS CLI commands is useful, but senior engineers are expected to solve real operational problems quickly.

This chapter contains production-ready CLI recipes that are commonly used by Backend Engineers, DevOps Engineers, SREs, and Cloud Engineers.

These examples can be used as:

- Runbooks
- Operational playbooks
- Deployment scripts
- CI/CD automation
- Disaster recovery procedures
- Maintenance scripts

Unlike previous chapters, this one focuses on **real-world operational scenarios**.

---

# Learning Objectives

After completing this chapter, you'll know how to:

- Verify deployments
- Create production backups
- Restore tables safely
- Enable production features
- Audit DynamoDB configuration
- Perform operational health checks
- Validate infrastructure
- Troubleshoot production issues
- Automate common maintenance tasks

---

# Recipe 1 — Verify Table Exists

Before deploying an application, verify the table exists.

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus" \
    --output text
```

Expected output:

```text
ACTIVE
```

Deployment workflow:

```text
Deployment

↓

Verify Table

↓

ACTIVE

↓

Continue Deployment
```

---

# Recipe 2 — Wait Until Table Is Ready

Instead of polling repeatedly:

```bash
aws dynamodb wait table-exists \
    --table-name Orders
```

Useful after:

- create-table
- restore-table
- infrastructure deployment

---

# Recipe 3 — Verify Billing Mode

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.BillingModeSummary.BillingMode"
```

Expected output:

```text
PAY_PER_REQUEST
```

Useful after Infrastructure as Code deployments.

---

# Recipe 4 — Check Item Count

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.ItemCount"
```

Useful for:

- Migration verification
- Import validation
- Restore verification

---

# Recipe 5 — Verify PITR

```bash
aws dynamodb describe-continuous-backups \
    --table-name Orders
```

Expected:

```text
PointInTimeRecoveryStatus

↓

ENABLED
```

Production recommendation:

Every production table should have PITR enabled.

---

# Recipe 6 — Verify TTL

```bash
aws dynamodb describe-time-to-live \
    --table-name Orders
```

Expected:

```text
TimeToLiveStatus

↓

ENABLED
```

---

# Recipe 7 — Verify Streams

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.StreamSpecification"
```

Useful for:

- Lambda integrations
- CDC pipelines
- Event-driven systems

---

# Recipe 8 — Create Deployment Backup

Before every production deployment:

```bash
aws dynamodb create-backup \
    --table-name Orders \
    --backup-name Orders-PreDeploy
```

Workflow:

```text
Production

↓

Create Backup

↓

Deploy

↓

Rollback Available
```

---

# Recipe 9 — List All Backups

```bash
aws dynamodb list-backups \
    --table-name Orders
```

Useful during:

- Disaster recovery
- Compliance audits
- Maintenance

---

# Recipe 10 — Restore Backup

```bash
aws dynamodb restore-table-from-backup \
    --target-table-name Orders-Restore \
    --backup-arn <BACKUP_ARN>
```

Always restore into a **new table**.

---

# Recipe 11 — Export to Amazon S3

```bash
aws dynamodb export-table-to-point-in-time \
    --table-arn <TABLE_ARN> \
    --s3-bucket analytics-bucket \
    --export-format DYNAMODB_JSON
```

Useful for:

- Athena
- EMR
- Data Lake
- Long-term archival

---

# Recipe 12 — View Table Size

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableSizeBytes"
```

Useful before:

- Migration
- Capacity planning
- Cost analysis

---

# Recipe 13 — View GSIs

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.GlobalSecondaryIndexes"
```

Verify:

- Index names
- Index status
- Capacity
- Projection type

---

# Recipe 14 — Query a GSI

```bash
aws dynamodb query \
    --table-name Orders \
    --index-name StatusIndex \
    --key-condition-expression \
        "status = :status" \
    --expression-attribute-values \
'{
":status":{"S":"SHIPPED"}
}'
```

Useful for validating new indexes after deployment.

---

# Recipe 15 — Check Service Limits

```bash
aws dynamodb describe-limits
```

Useful before:

- Scaling
- Capacity increases
- Large migrations

---

# Recipe 16 — Find All Tables

```bash
aws dynamodb list-tables
```

Useful when:

- Auditing environments
- Validating deployments
- Discovering resources

---

# Recipe 17 — Health Check Script

```bash
STATUS=$(aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus" \
    --output text)

if [ "$STATUS" = "ACTIVE" ]; then
    echo "Healthy"
else
    echo "Problem"
fi
```

Typical use:

```text
Monitoring

↓

Health Check

↓

Alert

↓

Engineer
```

---

# Recipe 18 — Deployment Validation

Production checklist:

```text
Describe Table

↓

ACTIVE

↓

Verify TTL

↓

Verify PITR

↓

Verify Streams

↓

Verify GSI

↓

Deploy Backend
```

---

# Recipe 19 — Daily Backup Script

```bash
TABLES=("Orders" "Customers" "Products")

for table in "${TABLES[@]}"
do
    aws dynamodb create-backup \
        --table-name "$table" \
        --backup-name "${table}-$(date +%F)"
done
```

Can be executed using:

- Cron
- GitHub Actions
- EventBridge Scheduler
- AWS Systems Manager

---

# Recipe 20 — Audit Production Tables

List table names:

```bash
aws dynamodb list-tables \
    --query "TableNames"
```

Loop through each table:

```bash
for table in $(aws dynamodb list-tables \
--query "TableNames[]" \
--output text)
do
    echo "$table"

    aws dynamodb describe-table \
        --table-name "$table" \
        --query "Table.TableStatus"
done
```

Useful during:

- Production audits
- Infrastructure reviews
- Compliance checks

---

# Complete Deployment Workflow

```text
Infrastructure Created

        │

        ▼

Wait For ACTIVE

        │

        ▼

Enable PITR

        │

        ▼

Enable TTL

        │

        ▼

Enable Streams

        │

        ▼

Create Deployment Backup

        │

        ▼

Verify GSIs

        │

        ▼

Run Smoke Tests

        │

        ▼

Deploy Application
```

---

# Disaster Recovery Workflow

```text
Incident

      │

      ▼

Identify Problem

      │

      ▼

Locate Backup

      │

      ▼

Restore New Table

      │

      ▼

Validate Data

      │

      ▼

Switch Traffic

      │

      ▼

Resume Production
```

---

# Operational Checklist

Daily:

- Verify table status
- Review CloudWatch alarms
- Confirm backup success

Weekly:

- Validate PITR
- Verify TTL
- Check table growth

Monthly:

- Test restore procedure
- Audit IAM permissions
- Review billing mode
- Review GSIs
- Validate disaster recovery documentation

---

# Performance Considerations

- Prefer Query over Scan during diagnostics.
- Avoid scanning large production tables.
- Use JMESPath (`--query`) to minimize output.
- Batch operational commands where possible.
- Automate recurring operational tasks.

---

# Security Best Practices

- Execute CLI commands using IAM Roles or least-privilege IAM users.
- Use separate AWS profiles for development, staging, and production.
- Protect backup resources with appropriate IAM policies.
- Log all administrative actions using CloudTrail.
- Never expose AWS credentials in scripts or repositories.

---

# Best Practices

- Create backups before production deployments.
- Verify infrastructure before releasing applications.
- Automate operational runbooks.
- Regularly test restore procedures.
- Keep operational scripts under version control.
- Standardize health check scripts across environments.

---

# Common Mistakes

## Deploying Without Verification

Always verify:

- Table status
- Index status
- PITR
- TTL
- Streams

before deploying production applications.

---

## Restoring Directly Into Production

Always restore to a new table first.

Validate:

- Data integrity
- Item count
- Application compatibility

before redirecting traffic.

---

## Ignoring Operational Documentation

Operational procedures should be:

- Version controlled
- Reviewed regularly
- Tested periodically

Runbooks are just as important as application code.

---

## Running Destructive Commands Against the Wrong Environment

Before executing commands such as:

```bash
delete-table
```

verify:

- AWS Profile
- AWS Region
- Table Name
- Target Environment

---

# Interview Notes

A common interview question is:

> **What operational checks would you perform before deploying a service that depends on DynamoDB?**

Verify that the table is `ACTIVE`, confirm the billing mode, ensure GSIs are active, verify that TTL and Point-in-Time Recovery are enabled, create an on-demand backup, and perform a smoke test against the table.

---

Another common question is:

> **Why should production deployments create an on-demand backup even when PITR is enabled?**

An on-demand backup provides a fixed recovery point immediately before the deployment, making rollbacks simpler and providing an additional layer of protection alongside continuous recovery.

---

Another common question is:

> **How would you validate a restored DynamoDB table before using it in production?**

Check the table status, compare the item count with the source table, verify indexes, test application queries, and ensure data integrity before switching production traffic.

---

Another common question is:

> **Why are CLI runbooks valuable in production environments?**

CLI runbooks provide standardized, repeatable operational procedures that reduce human error, improve incident response, and simplify automation across teams.

---

# Key Takeaways

- Production engineers rely on repeatable CLI recipes to manage DynamoDB safely and efficiently.
- Common operational tasks include health checks, backups, restores, deployment validation, and infrastructure audits.
- Automation and version-controlled runbooks reduce operational risk and improve consistency.
- Regular validation of backups, disaster recovery procedures, and table configurations is essential for production reliability.
- Mastering these CLI recipes prepares engineers for real-world operations, incident response, and senior-level AWS responsibilities.