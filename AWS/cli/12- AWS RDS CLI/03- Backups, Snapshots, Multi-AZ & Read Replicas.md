# Backups, Snapshots, Multi-AZ & Read Replicas

> Learn how Amazon RDS protects data using automated backups, manual snapshots, Multi-AZ deployments, and Read Replicas. This chapter covers backup strategies, disaster recovery, failover, replication, point-in-time recovery (PITR), and production best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Configure automated backups
- Create manual snapshots
- Restore databases
- Understand Point-in-Time Recovery
- Configure Multi-AZ deployments
- Create Read Replicas
- Build highly available production databases

---

# Data Protection Strategy

Production databases require multiple layers of protection.

```text
Amazon RDS

│

├── Automated Backups

├── Manual Snapshots

├── Multi-AZ

└── Read Replicas
```

---

# Automated Backups

Amazon RDS automatically performs:

- Daily backups
- Transaction log backups

These backups enable:

```text
Point-in-Time Recovery (PITR)
```

---

# Backup Workflow

```text
Database

↓

Daily Backup

↓

S3 Managed Storage

↓

Recovery
```

AWS manages backup storage automatically.

---

# Backup Retention Period

Retention can be configured from:

```text
1 Day

↓

35 Days
```

Typical values:

| Environment | Retention |
|-------------|-----------|
| Development | 1–3 Days |
| Testing | 7 Days |
| Production | 14–35 Days |

---

# View Backup Settings

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Review:

- BackupRetentionPeriod
- PreferredBackupWindow

---

# Modify Backup Retention

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--backup-retention-period 14
```

---

# Backup Window

Backups occur during a preferred window.

Example:

```text
02:00

↓

03:00 UTC
```

Choose periods with low database activity.

---

# Manual Snapshots

Manual snapshots are created on demand.

Unlike automated backups:

- They never expire
- They remain until deleted

---

# Snapshot Workflow

```text
Database

↓

Manual Snapshot

↓

Stored

↓

Restore Anytime
```

---

# Create Snapshot

```bash
aws rds create-db-snapshot \
--db-instance-identifier production-db \
--db-snapshot-identifier production-db-before-upgrade
```

---

# List Snapshots

```bash
aws rds describe-db-snapshots
```

---

# Describe Snapshot

```bash
aws rds describe-db-snapshots \
--db-snapshot-identifier production-db-before-upgrade
```

---

# Delete Snapshot

```bash
aws rds delete-db-snapshot \
--db-snapshot-identifier production-db-before-upgrade
```

---

# Restore from Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot \
--db-instance-identifier restored-db \
--db-snapshot-identifier production-db-before-upgrade
```

---

# Snapshot Architecture

```text
Production Database

↓

Snapshot

↓

Restore

↓

New Database
```

Snapshots never overwrite the original database.

---

# Point-in-Time Recovery (PITR)

Amazon RDS can restore a database to any specific point within the backup retention period.

Example:

```text
09:30 AM

↓

Database Deleted

↓

Restore to

↓

09:29 AM
```

---

# Restore to Point in Time

```bash
aws rds restore-db-instance-to-point-in-time \
--source-db-instance-identifier production-db \
--target-db-instance-identifier restored-db
```

---

# Recovery Workflow

```text
Automated Backup

↓

Transaction Logs

↓

Specific Time

↓

Recovered Database
```

---

# Multi-AZ Deployment

Multi-AZ provides high availability.

Architecture:

```text
Primary

↓

Synchronous Replication

↓

Standby
```

---

# Multi-AZ Architecture

```text
Application

↓

Primary DB

↓

Standby DB

↓

Shared Storage
```

The standby database cannot be used for queries.

---

# Benefits of Multi-AZ

- Automatic failover
- High availability
- Managed replication
- Reduced downtime
- Disaster recovery

---

# Enable Multi-AZ

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--multi-az
```

---

# Failover Workflow

```text
Primary Failure

↓

Automatic Detection

↓

Standby Promotion

↓

New Primary
```

Applications reconnect using the same endpoint.

---

# Multi-AZ vs Single-AZ

| Feature | Single-AZ | Multi-AZ |
|----------|-----------|----------|
| High Availability | ❌ | ✅ |
| Automatic Failover | ❌ | ✅ |
| Cost | Lower | Higher |
| Production | Not Recommended | Recommended |

---

# Read Replicas

Read Replicas improve read performance.

Architecture:

```text
Primary

↓

Asynchronous Replication

↓

Read Replica
```

---

# Read Replica Workflow

```text
Write

↓

Primary

↓

Replication

↓

Read Replica
```

Applications send read-only queries to replicas.

---

# Create Read Replica

```bash
aws rds create-db-instance-read-replica \
--db-instance-identifier production-replica \
--source-db-instance-identifier production-db
```

---

# Read Replica Architecture

```text
Application

│

├── Writes

│      ↓

│   Primary

│

└── Reads

       ↓

Read Replica
```

---

# Read Replica Benefits

- Read scaling
- Reporting
- Analytics
- Backup offloading
- Reduced load on primary

---

# Promote Read Replica

```bash
aws rds promote-read-replica \
--db-instance-identifier production-replica
```

After promotion:

```text
Replica

↓

Standalone Database
```

---

# Multi-AZ vs Read Replica

| Feature | Multi-AZ | Read Replica |
|----------|-----------|--------------|
| Purpose | High Availability | Read Scaling |
| Replication | Synchronous | Asynchronous |
| Automatic Failover | Yes | No |
| Read Queries | No | Yes |

---

# Cross-Region Read Replicas

Architecture:

```text
Mumbai

↓

Primary

↓

Replication

↓

Singapore

↓

Replica
```

Useful for:

- Global applications
- Disaster recovery
- Regional reporting

---

# Backup Strategy

Typical production strategy:

```text
Automated Backup

↓

Manual Snapshot

↓

Multi-AZ

↓

Read Replica
```

Multiple protection layers improve resilience.

---

# Common Errors

## SnapshotAlreadyExists

Choose a unique snapshot identifier.

---

## DBSnapshotNotFound

Verify:

- Snapshot identifier
- Region
- Account

---

## BackupRetentionPeriodNotEnabled

Enable automated backups before using PITR.

---

## ReadReplicaAlreadyExists

Verify replica identifiers.

---

## Multi-AZ Modification Failed

Verify:

- Instance class
- Storage availability
- Region capacity

---

# Production Best Practices

- Enable automated backups.
- Retain backups for at least 7–14 days.
- Take manual snapshots before upgrades.
- Use Multi-AZ for all production databases.
- Use Read Replicas for read-heavy workloads.
- Test database restores regularly.
- Monitor replication lag.
- Store snapshots before major schema changes.
- Enable cross-region replicas for disaster recovery.

---

# Real-World Workflow

```text
Create Database

↓

Enable Backups

↓

Configure Multi-AZ

↓

Create Read Replica

↓

Production

↓

Manual Snapshots Before Changes
```

---

# Architecture Note

```text
Application
      │
      ▼
Primary RDS
      │
      ├── Automated Backups
      ├── Manual Snapshots
      ├── Multi-AZ Standby
      └── Read Replica
```

Production RDS deployments typically combine automated backups, manual snapshots, Multi-AZ failover, and Read Replicas to achieve high availability, disaster recovery, and scalable read performance.

---

# Interview Note

### Question

**What is the difference between Multi-AZ and Read Replicas in Amazon RDS?**

### Answer

**Multi-AZ** is designed for **high availability and automatic failover**. It synchronously replicates data to a standby instance in another Availability Zone, and the standby cannot serve read traffic. **Read Replicas** are designed for **read scalability**. They asynchronously replicate data from the primary database and can serve read-only queries, but they do not automatically replace the primary instance during a failure.

---

# Key Takeaways

- Automated backups enable Point-in-Time Recovery.
- Manual snapshots never expire unless deleted.
- Multi-AZ provides high availability and automatic failover.
- Read Replicas improve read scalability but do not provide automatic failover.
- Applications continue using the same endpoint after a Multi-AZ failover.
- Manual snapshots should be taken before major upgrades or schema changes.
- A combination of backups, snapshots, Multi-AZ, and Read Replicas provides a robust production-grade data protection strategy.