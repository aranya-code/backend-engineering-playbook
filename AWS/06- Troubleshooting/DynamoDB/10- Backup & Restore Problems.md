# 10 - Backup & Restore Problems

## Overview

Amazon DynamoDB provides multiple mechanisms for protecting data against accidental deletion, corruption, and disasters.

These include:

- On-Demand Backups
- Point-in-Time Recovery (PITR)
- Table Restore
- Export to Amazon S3
- AWS Backup integration

While these features are highly reliable, production issues often arise from misunderstandings about how backup and restore operations work.

This chapter covers the most common backup and restore problems, how to troubleshoot them, and production best practices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- On-Demand Backups
- Point-in-Time Recovery (PITR)
- Restore operations
- Backup troubleshooting
- Export troubleshooting
- Disaster recovery
- Monitoring
- Production best practices

---

# Backup Architecture

```text
                Amazon DynamoDB

                       │

        ┌──────────────┼──────────────┐

        ▼                             ▼

 On-Demand Backup          Point-in-Time Recovery

        │                             │

        ▼                             ▼

       Backup                    Continuous Log

        │

        ▼

Restore Table
```

---

# Backup Options

| Feature | Purpose |
|----------|----------|
| On-Demand Backup | Manual snapshot |
| PITR | Restore to any second within the retention window |
| Export to S3 | Data lake, analytics, migration |
| AWS Backup | Centralized backup management |

---

# Common Problems

Production issues typically involve:

- Backup missing
- PITR disabled
- Restore delays
- Missing indexes
- Wrong Region
- Wrong account
- Restore expectations
- Export failures

---

# Problem 1 — Backup Not Found

Symptoms:

```text
Restore Backup

↓

Backup Missing
```

Verify backups:

```bash
aws dynamodb list-backups
```

Review:

- Backup name
- Backup ARN
- Creation date
- Status

---

# Problem 2 — PITR Disabled

Many teams assume PITR is enabled automatically.

Verify:

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

---

# Problem 3 — Restore Creates a New Table

A common misconception:

```text
Restore

↓

Overwrite Existing Table
```

Incorrect.

Actual behavior:

```text
Restore

↓

Creates New Table
```

You must migrate traffic to the restored table if required.

---

# Restore Workflow

```text
Backup

↓

Restore

↓

New Table

↓

Validation

↓

Application Cutover
```

---

# Problem 4 — Restore Takes Time

Large tables:

```text
5 TB

↓

Restore

↓

Several Hours
```

Restore duration depends on:

- Table size
- Item count
- AWS infrastructure

---

# Problem 5 — Wrong Region

Backup:

```text
us-east-1
```

Attempt:

```text
Restore

↓

eu-west-1
```

Result:

```text
Backup Not Found
```

Always verify Region.

---

# Problem 6 — Wrong AWS Account

Production:

```text
Account A
```

Restore attempt:

```text
Account B
```

Result:

```text
No Backup Found
```

Check identity:

```bash
aws sts get-caller-identity
```

---

# Problem 7 — Missing PITR Window

PITR only retains data within its configured recovery window.

Example:

```text
Today

↓

Recover Data

↓

45 Days Ago
```

Impossible if the recovery window has already expired.

---

# Problem 8 — Export Failure

Export workflow:

```text
DynamoDB

↓

Export

↓

Amazon S3
```

Common causes:

- Incorrect S3 bucket policy
- Missing IAM permissions
- KMS encryption issues
- Wrong Region

---

# Verify Export

```bash
aws dynamodb list-exports
```

Review:

- Export status
- Failure reason
- Destination bucket

---

# Monitoring

Useful CloudWatch metrics:

- Backup success
- Restore duration
- Export completion
- Failed restore attempts

Also monitor:

- AWS Backup jobs
- CloudTrail events

---

# Investigation Workflow

```text
Restore Failed

↓

Backup Exists?

↓

Correct Region?

↓

Correct Account?

↓

IAM Permissions?

↓

PITR Enabled?

↓

Root Cause
```

---

# Disaster Recovery Example

Production outage:

```text
Accidental Delete

↓

PITR

↓

Restore Table

↓

Validation

↓

Traffic Switched

↓

Recovery Complete
```

---

# Accidental Data Deletion

```text
Application Bug

↓

Delete Thousands of Items

↓

PITR Restore

↓

Recovered Data
```

Without PITR:

```text
Permanent Data Loss
```

---

# Production Example

Order table:

```text
Orders

↓

Developer Mistake

↓

Delete Table
```

Recovery:

```text
Latest Backup

↓

Restore

↓

Orders-Restored

↓

Deploy

↓

Update Configuration

↓

Production Restored
```

---

# Backup Strategy

Recommended architecture:

```text
Production

      │

      ▼

PITR Enabled

      │

      ▼

Daily Backup

      │

      ▼

Export to S3

      │

      ▼

Cross-Region Storage
```

Provides multiple recovery options.

---

# Recovery Checklist

Verify:

- Backup exists
- PITR enabled
- Region
- Account
- IAM permissions
- KMS access
- Table validation
- Application configuration

---

# Performance Considerations

- Enabling PITR has minimal operational impact but adds storage cost.
- Restores create new tables and may require application changes.
- Large restores can take considerable time.
- Exports are asynchronous operations.
- Test disaster recovery procedures regularly.

---

# Best Practices

- Enable PITR on production tables.
- Take on-demand backups before major deployments.
- Automate backups using AWS Backup.
- Store exports in Amazon S3.
- Test restores regularly.
- Document disaster recovery procedures.
- Monitor backup jobs and failures.

---

# Common Mistakes

## Assuming Restore Overwrites the Existing Table

Restores always create a **new table**.

---

## Never Testing Restores

A backup is only useful if it can be restored successfully.

Practice recovery drills regularly.

---

## Disabling PITR to Save Costs

The cost savings are often insignificant compared to the impact of losing production data.

---

## Forgetting Cross-Region Recovery

Regional outages can affect recovery if all backups remain in the same Region.

---

## Ignoring IAM Permissions

Backup and restore operations require appropriate permissions on DynamoDB, S3, and KMS resources.

---

# Interview Notes

### What backup options does DynamoDB provide?

- On-Demand Backups
- Point-in-Time Recovery (PITR)
- Export to Amazon S3
- AWS Backup integration

---

### Does restoring a backup overwrite an existing table?

No.

A restore operation always creates a new table.

---

### What is Point-in-Time Recovery?

PITR continuously captures changes, allowing a table to be restored to any second within the configured recovery window.

---

### How would you recover from accidental table deletion?

Restore the latest backup or use PITR (if enabled), validate the restored table, and redirect application traffic to the new table.

---

### Why should disaster recovery procedures be tested regularly?

Backups are only valuable if they can be successfully restored within acceptable recovery objectives (RTO/RPO). Regular testing validates both the backup data and operational runbooks.

---

# Key Takeaways

- DynamoDB provides multiple backup and recovery mechanisms for different recovery scenarios.
- Point-in-Time Recovery is one of the most valuable safeguards for production environments and should be enabled on critical tables.
- Restore operations create new tables rather than replacing existing ones, requiring validation and application cutover.
- Successful disaster recovery depends not only on backups but also on tested procedures, proper IAM permissions, and monitoring.
- Senior backend engineers design backup strategies that align with business continuity requirements and regularly validate recovery processes.