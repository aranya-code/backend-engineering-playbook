# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon RDS CLI commands, database administration workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, Database Administrators (DBAs), and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used Amazon RDS CLI commands
- Manage DB Instances
- Configure backups and snapshots
- Monitor databases
- Scale infrastructure
- Troubleshoot production databases
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon RDS includes many operational components:

- DB Instances
- Storage
- Networking
- Security
- Snapshots
- Backups
- Multi-AZ
- Read Replicas
- Monitoring

Experienced engineers focus on:

- Database lifecycle
- High Availability
- Disaster Recovery
- Performance optimization
- Security
- Monitoring

This chapter provides a practical operational reference.

---

# CLI Namespace

General syntax:

```bash
aws rds <operation>
```

Examples:

```bash
aws rds describe-db-instances
```

```bash
aws rds create-db-instance
```

```bash
aws rds create-db-snapshot
```

---

# DB Instance Commands

## List Databases

```bash
aws rds describe-db-instances
```

---

## Create Database

```bash
aws rds create-db-instance
```

---

## Describe Database

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

---

## Modify Database

```bash
aws rds modify-db-instance
```

---

## Delete Database

```bash
aws rds delete-db-instance
```

---

## Reboot Database

```bash
aws rds reboot-db-instance
```

---

## Force Multi-AZ Failover

```bash
aws rds reboot-db-instance \
--force-failover
```

---

# Backup Commands

## View Backup Configuration

```bash
aws rds describe-db-instances
```

---

## Modify Backup Retention

```bash
aws rds modify-db-instance \
--backup-retention-period 14
```

---

# Snapshot Commands

## Create Snapshot

```bash
aws rds create-db-snapshot
```

---

## List Snapshots

```bash
aws rds describe-db-snapshots
```

---

## Restore Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot
```

---

## Delete Snapshot

```bash
aws rds delete-db-snapshot
```

---

# Point-in-Time Recovery

## Restore Database

```bash
aws rds restore-db-instance-to-point-in-time
```

---

# Read Replica Commands

## Create Read Replica

```bash
aws rds create-db-instance-read-replica
```

---

## Promote Read Replica

```bash
aws rds promote-read-replica
```

---

# DB Subnet Group Commands

## List Subnet Groups

```bash
aws rds describe-db-subnet-groups
```

---

## Create Subnet Group

```bash
aws rds create-db-subnet-group
```

---

# Parameter Group Commands

## List Parameter Groups

```bash
aws rds describe-db-parameter-groups
```

---

## Create Parameter Group

```bash
aws rds create-db-parameter-group
```

---

## Modify Parameter Group

```bash
aws rds modify-db-parameter-group
```

---

# Option Group Commands

## List Option Groups

```bash
aws rds describe-option-groups
```

---

## Create Option Group

```bash
aws rds create-option-group
```

---

# Monitoring Commands

## View Events

```bash
aws rds describe-events
```

---

## View Log Files

```bash
aws rds describe-db-log-files
```

---

## Download Log File

```bash
aws rds download-db-log-file-portion
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use named AWS profile |
| `--region` | Override Region |
| `--query` | Filter CLI output |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--debug` | Enable debugging |
| `--no-cli-pager` | Disable pager |

---

# Amazon RDS Components

| Component | Purpose |
|-----------|----------|
| DB Instance | Database compute resource |
| Endpoint | Database connection endpoint |
| Storage | Persistent database storage |
| DB Subnet Group | Network placement |
| Parameter Group | Database configuration |
| Option Group | Engine-specific features |
| Security Group | Network security |
| Read Replica | Read scaling |
| Multi-AZ | High availability |

---

# Storage Types

| Storage | Best Use |
|----------|----------|
| gp3 | Most workloads |
| io1 | High IOPS |
| io2 | Enterprise workloads |
| Magnetic | Legacy only |

---

# High Availability Comparison

| Feature | Single-AZ | Multi-AZ | Read Replica |
|----------|-----------|----------|--------------|
| High Availability | ❌ | ✅ | ❌ |
| Automatic Failover | ❌ | ✅ | ❌ |
| Read Scaling | ❌ | ❌ | ✅ |
| Disaster Recovery | Limited | Excellent | Moderate |

---

# Common CloudWatch Metrics

| Metric | Purpose |
|---------|----------|
| CPUUtilization | CPU usage |
| DatabaseConnections | Active connections |
| FreeStorageSpace | Remaining storage |
| ReadIOPS | Read performance |
| WriteIOPS | Write performance |
| ReadLatency | Read latency |
| WriteLatency | Write latency |
| ReplicaLag | Replica health |

---

# Recommended CloudWatch Alarms

- CPU > 80%
- Storage < 20%
- High Connection Count
- Replica Lag
- High Read Latency
- High Write Latency

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| DBInstanceNotFound | Invalid instance | Verify identifier |
| DBSnapshotNotFound | Snapshot missing | Verify snapshot |
| InvalidDBInstanceState | Database busy | Wait for Available state |
| AccessDenied | IAM issue | Review IAM permissions |
| InsufficientStorage | Storage exhausted | Increase storage |
| TooManyConnections | Connection limit reached | Use RDS Proxy |
| Authentication Failed | Invalid credentials | Verify username/password |
| KMSKeyNotAccessible | Encryption issue | Verify KMS permissions |

---

# Backup Strategy

```text
Daily Automated Backup

↓

Transaction Logs

↓

Point-in-Time Recovery

↓

Manual Snapshot

↓

Long-Term Backup
```

---

# Disaster Recovery Workflow

```text
Database Failure

↓

CloudWatch Alarm

↓

Restore Snapshot

↓

Application Validation

↓

Production
```

---

# Multi-AZ Architecture

```text
Application

↓

Primary

↓

Synchronous Replication

↓

Standby
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

# Monitoring Workflow

```text
Amazon RDS

↓

CloudWatch

↓

Alarm

↓

SNS

↓

Operations Team
```

---

# Production Checklist

Every production database should include:

- □ Multi-AZ enabled
- □ Automated backups
- □ Manual snapshots before upgrades
- □ Storage Auto Scaling
- □ Private subnets
- □ Security Groups
- □ AWS KMS encryption
- □ CloudWatch alarms
- □ Enhanced Monitoring
- □ Performance Insights
- □ Secrets Manager
- □ RDS Proxy (when needed)

---

# Daily DBA Checklist

Review:

- Database availability
- CPU utilization
- Storage utilization
- Slow queries
- Replica lag
- Backup completion
- Connection count
- Recent events

---

# Weekly DBA Checklist

Review:

- Parameter Groups
- Security Groups
- Snapshot cleanup
- Maintenance schedule
- Storage growth
- CloudWatch alarms
- Performance trends

---

# Production Architecture

```text
Application
      │
      ▼
AWS Secrets Manager
      │
      ▼
Amazon RDS Proxy
      │
      ▼
Amazon RDS
      │
      ├── Multi-AZ
      ├── CloudWatch
      ├── Enhanced Monitoring
      ├── Performance Insights
      ├── Automated Backups
      └── AWS KMS
```

---

# Interview Questions

## 1. What is Amazon RDS?

**Answer**

Amazon RDS is AWS's managed relational database service that automates provisioning, backups, patching, monitoring, scaling, and high availability for supported relational database engines.

---

## 2. What is the difference between Multi-AZ and Read Replicas?

**Answer**

Multi-AZ provides synchronous replication and automatic failover for high availability. Read Replicas use asynchronous replication to improve read performance and do not provide automatic failover.

---

## 3. What is Point-in-Time Recovery (PITR)?

**Answer**

Point-in-Time Recovery restores an RDS database to any specific point within the configured backup retention period by combining automated backups with transaction logs.

---

## 4. Why should applications connect using the RDS endpoint instead of an IP address?

**Answer**

The RDS endpoint is a stable DNS name that automatically resolves to the active database instance. During Multi-AZ failover, AWS updates the endpoint automatically, allowing applications to reconnect without changing connection settings.

---

## 5. What is a DB Subnet Group?

**Answer**

A DB Subnet Group is a collection of subnets within a VPC where Amazon RDS is allowed to deploy database instances. Production subnet groups should span multiple Availability Zones.

---

## 6. What is the purpose of a Parameter Group?

**Answer**

A Parameter Group contains database engine configuration values such as connection limits, logging options, memory settings, and query behavior. Custom Parameter Groups allow database tuning without modifying default configurations.

---

## 7. What is Amazon RDS Proxy?

**Answer**

Amazon RDS Proxy is a managed connection pool that improves application scalability by reducing the number of direct database connections, handling connection reuse, and improving failover times.

---

## 8. How do you secure an Amazon RDS database?

**Answer**

Production databases should be deployed in private subnets, protected by Security Groups, encrypted using AWS KMS, accessed through SSL/TLS connections, and integrated with IAM authentication or AWS Secrets Manager for credential management.

---

## 9. How would you troubleshoot an application that cannot connect to an Amazon RDS database?

**Answer**

I would verify the DB instance status, confirm the endpoint, inspect Security Groups, subnet routing, and DNS resolution, validate credentials or IAM authentication, review CloudWatch metrics and recent RDS events, and use Performance Insights or database logs to identify any underlying issues.

---

## 10. How would you safely upgrade a production Amazon RDS database?

**Answer**

I would create a manual snapshot, test the upgrade in a staging environment, use Blue/Green deployments if supported, schedule the change during the maintenance window, monitor CloudWatch metrics during the upgrade, and keep a rollback plan based on the pre-upgrade snapshot.

---

# Senior Engineer Tips

Experienced database engineers typically:

- Use Multi-AZ for every production database.
- Deploy RDS instances only in private subnets.
- Enable automated backups and Performance Insights.
- Create manual snapshots before upgrades.
- Store credentials in AWS Secrets Manager.
- Use RDS Proxy for high-concurrency workloads.
- Monitor slow queries continuously.
- Tune databases using custom Parameter Groups.
- Test disaster recovery procedures regularly.
- Plan capacity before resource limits are reached.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Databases | `aws rds describe-db-instances` |
| Create Database | `aws rds create-db-instance` |
| Modify Database | `aws rds modify-db-instance` |
| Reboot Database | `aws rds reboot-db-instance` |
| Create Snapshot | `aws rds create-db-snapshot` |
| Restore Snapshot | `aws rds restore-db-instance-from-db-snapshot` |
| Restore to PITR | `aws rds restore-db-instance-to-point-in-time` |
| Create Read Replica | `aws rds create-db-instance-read-replica` |
| Describe Events | `aws rds describe-events` |
| Download Logs | `aws rds download-db-log-file-portion` |

---

# Final Thoughts

Amazon RDS simplifies the operational management of relational databases by automating provisioning, backups, monitoring, maintenance, and high availability. Combined with AWS KMS, CloudWatch, Performance Insights, Secrets Manager, RDS Proxy, and Multi-AZ deployments, Amazon RDS enables organizations to run secure, scalable, and resilient production databases with significantly less operational overhead.

---
