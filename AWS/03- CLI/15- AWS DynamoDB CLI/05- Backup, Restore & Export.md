# 05 - Backup, Restore & Export

## Overview

Data protection is a critical aspect of operating production databases. Although Amazon DynamoDB is a highly durable, managed NoSQL database, engineers must still prepare for scenarios such as:

- Accidental deletions
- Corrupted deployments
- Application bugs
- Human errors
- Disaster recovery
- Compliance requirements
- Data migration
- Analytics workloads

The AWS CLI provides commands to create backups, restore tables, export data to Amazon S3, and import data into DynamoDB.

Understanding these operations is essential for building resilient production systems.

---

# Learning Objectives

After completing this chapter, you'll understand:

- On-Demand Backups
- Point-in-Time Recovery (PITR)
- Restoring tables
- Exporting data to Amazon S3
- Importing data
- Listing backups
- Disaster recovery workflows
- Production best practices

---

# Backup Strategies

DynamoDB supports two primary backup mechanisms.

```text
                DynamoDB

                     │

        ┌────────────┴─────────────┐

        ▼                          ▼

On-Demand Backup          Point-in-Time Recovery

        │                          │

Manual Snapshot          Continuous Backup

```

---

# Types of Backups

| Backup Type | Automatic | Recovery Point | Typical Use Case |
|--------------|-----------|----------------|------------------|
| On-Demand Backup | ❌ | Snapshot Time | Manual backups before deployments |
| Point-in-Time Recovery | ✅ | Any second within retention window | Continuous disaster recovery |

---

# Creating an On-Demand Backup

Basic syntax:

```bash
aws dynamodb create-backup \
    --table-name Orders \
    --backup-name Orders-2026-07-26
```

Example response:

```json
{
    "BackupDetails": {
        "BackupName": "Orders-2026-07-26",
        "BackupStatus": "CREATING"
    }
}
```

---

# Backup Lifecycle

```text
ACTIVE TABLE

      │

      ▼

Create Backup

      │

      ▼

CREATING

      │

      ▼

AVAILABLE
```

---

# Listing Backups

View backups for a table.

```bash
aws dynamodb list-backups \
    --table-name Orders
```

Example response:

```json
{
    "BackupSummaries": [
        {
            "BackupName": "Orders-2026-07-26"
        }
    ]
}
```

---

# Describing a Backup

Retrieve metadata.

```bash
aws dynamodb describe-backup \
    --backup-arn <BACKUP_ARN>
```

Information includes:

- Backup size
- Creation date
- Backup status
- Source table
- Table schema

---

# Deleting a Backup

Delete an unused backup.

```bash
aws dynamodb delete-backup \
    --backup-arn <BACKUP_ARN>
```

Use caution—this action is irreversible.

---

# Point-in-Time Recovery (PITR)

PITR continuously records table changes.

```text
Table

↓

Continuous Backup

↓

Recovery Window

↓

Restore
```

Instead of restoring to a snapshot, you restore to a specific point in time.

---

# Enabling PITR

```bash
aws dynamodb update-continuous-backups \
    --table-name Orders \
    --point-in-time-recovery-specification \
PointInTimeRecoveryEnabled=true
```

---

# Viewing PITR Status

```bash
aws dynamodb describe-continuous-backups \
    --table-name Orders
```

Example:

```json
{
    "ContinuousBackupsDescription": {
        "PointInTimeRecoveryDescription": {
            "PointInTimeRecoveryStatus": "ENABLED"
        }
    }
}
```

---

# Restoring From an On-Demand Backup

A restore always creates a **new table**.

```bash
aws dynamodb restore-table-from-backup \
    --target-table-name Orders-Restore \
    --backup-arn <BACKUP_ARN>
```

---

# Restore Workflow

```text
Backup

      │

      ▼

Restore

      │

      ▼

New Table

      │

      ▼

Production Validation
```

The original table remains unchanged.

---

# Restoring Using PITR

Restore to a specific timestamp.

```bash
aws dynamodb restore-table-to-point-in-time \
    --source-table-name Orders \
    --target-table-name Orders-Restore \
    --restore-date-time "2026-07-26T08:30:00Z"
```

Useful after:

- Accidental deletes
- Faulty deployments
- Data corruption

---

# Monitoring Restore Progress

```bash
aws dynamodb describe-table \
    --table-name Orders-Restore
```

Wait until:

```text
ACTIVE
```

before using the restored table.

---

# Exporting to Amazon S3

Export table data without consuming read capacity.

```bash
aws dynamodb export-table-to-point-in-time \
    --table-arn <TABLE_ARN> \
    --s3-bucket backup-bucket \
    --export-format DYNAMODB_JSON
```

Supported export formats include:

- DYNAMODB_JSON
- ION

---

# Export Workflow

```text
DynamoDB

      │

      ▼

Export

      │

      ▼

Amazon S3

      │

      ▼

Analytics / Archive
```

---

# Importing From Amazon S3

Create a new table from exported data.

```bash
aws dynamodb import-table \
    --s3-bucket-source \
S3Bucket=backup-bucket,S3KeyPrefix=exports/ \
    --input-format DYNAMODB_JSON
```

Common use cases:

- Migration
- Data recovery
- Testing
- Environment cloning

---

# Disaster Recovery Workflow

```text
Production Table

      │

      ▼

Continuous Backup

      │

      ▼

Accidental Deletion

      │

      ▼

Restore

      │

      ▼

Validate

      │

      ▼

Resume Service
```

---

# Typical Production Workflow

```text
Deployment

↓

Create Backup

↓

Deploy Application

↓

Monitor

↓

Rollback if Required
```

Many teams take an on-demand backup immediately before major schema or application changes.

---

# Backup vs Export

| Feature | Backup | Export |
|----------|---------|---------|
| Disaster Recovery | ✅ | ❌ |
| Analytics | ❌ | ✅ |
| Restore Table | ✅ | ❌ |
| S3 Output | ❌ | ✅ |
| Migration | Limited | ✅ |

---

# Automation Example

Nightly backup script:

```bash
aws dynamodb create-backup \
    --table-name Orders \
    --backup-name Orders-$(date +%F)
```

This can be scheduled using:

- Cron
- GitHub Actions
- AWS Systems Manager
- EventBridge Scheduler

---

# Production Architecture

```text
CI/CD Pipeline

        │

        ▼

AWS CLI

        │

        ▼

Create Backup

        │

        ▼

Deploy Application

        │

        ▼

Rollback if Necessary
```

---

# Performance Considerations

- Enable PITR for all production tables.
- Create on-demand backups before risky deployments.
- Export to S3 for analytics instead of scanning production tables.
- Monitor restore duration for large tables.
- Validate restored tables before directing production traffic.

---

# Security Best Practices

- Encrypt S3 export buckets.
- Restrict backup and restore permissions using IAM.
- Enable CloudTrail logging for backup operations.
- Apply least-privilege IAM policies.
- Protect backup resources from accidental deletion.

---

# Best Practices

- Enable PITR on production tables.
- Take manual backups before major releases.
- Test restore procedures regularly.
- Export historical data to S3 for long-term retention.
- Automate backup creation and verification.
- Document disaster recovery procedures.

---

# Common Mistakes

## Assuming PITR Replaces Manual Backups

PITR provides continuous recovery but does not eliminate the need for manual backups before major deployments or migrations.

---

## Restoring Directly Over Production

A restore operation creates a new table.

Always:

1. Restore.
2. Validate.
3. Switch traffic if appropriate.

---

## Never Testing Restores

A backup is only useful if it can be successfully restored.

Perform periodic disaster recovery drills.

---

## Ignoring Export Costs

Exports to S3 are excellent for analytics and archival but should be planned with storage lifecycle policies and access controls.

---

# Interview Notes

A common interview question is:

> **What is the difference between an On-Demand Backup and Point-in-Time Recovery?**

An On-Demand Backup creates a manual snapshot of a table at a specific moment. Point-in-Time Recovery continuously records changes, allowing restoration to any second within the retention window.

---

Another common question is:

> **Does restoring a backup overwrite the existing table?**

No. DynamoDB always restores to a new table. The original table remains unchanged.

---

Another common question is:

> **When would you export a DynamoDB table to Amazon S3 instead of creating a backup?**

Exports are intended for analytics, long-term archival, migration, or integration with services like Athena and EMR. Backups are intended for disaster recovery.

---

Another common question is:

> **Why should production teams regularly test restore procedures?**

Because backups are only valuable if they can be restored successfully within the organization's recovery objectives. Regular testing verifies both the backup integrity and the recovery process.

---

# Key Takeaways

- DynamoDB provides both manual snapshots and continuous recovery mechanisms for protecting data.
- On-Demand Backups are useful before deployments and migrations, while PITR provides continuous recovery for operational failures.
- Restores always create new tables, enabling safe validation before production cutovers.
- Exporting data to Amazon S3 is ideal for analytics, archival, and migration without impacting table performance.
- A robust disaster recovery strategy includes automated backups, regular restore testing, secure storage, and documented operational procedures.