# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon RDS deployments, diagnose connectivity issues, resolve performance bottlenecks, recover from failures, and apply production-ready operational best practices using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot RDS connectivity
- Diagnose database failures
- Resolve backup and snapshot issues
- Troubleshoot replication
- Debug performance problems
- Recover databases
- Apply production operational best practices

---

# RDS Troubleshooting Workflow

Always troubleshoot from the client toward the database.

```text
Application

↓

DNS

↓

VPC

↓

Security Group

↓

RDS Endpoint

↓

Database Engine

↓

Storage
```

---

# Verify DB Instance

List databases.

```bash
aws rds describe-db-instances
```

Describe one database.

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Verify:

- Status
- Endpoint
- Engine
- Storage
- Multi-AZ
- Security Groups

---

# DB Instance Status

Common states:

```text
Creating
```

```text
Available
```

```text
Backing-up
```

```text
Modifying
```

```text
Rebooting
```

```text
Deleting
```

Only **Available** instances accept connections.

---

# Cannot Connect to Database

Troubleshooting order:

```text
DNS

↓

Endpoint

↓

Security Group

↓

Route Table

↓

Subnet

↓

Database Port
```

---

# Verify Endpoint

Retrieve endpoint.

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Example:

```text
production-db.xxxxxx.ap-south-1.rds.amazonaws.com
```

Applications should always connect using this endpoint.

---

# DNS Issues

Verify:

- Endpoint spelling
- Region
- VPC DNS enabled

Never connect using an IP address.

---

# Security Group Problems

Verify inbound rules.

Example PostgreSQL:

```text
Port

↓

5432
```

Only allow traffic from:

```text
Application Security Group
```

Avoid:

```text
0.0.0.0/0
```

for production.

---

# Network Connectivity

Verify:

- VPC
- Subnets
- Route Tables
- NACLs
- VPN/Direct Connect (if applicable)

Architecture:

```text
Application

↓

Private Subnet

↓

Amazon RDS
```

---

# Public Access Problems

Check:

```text
Publicly Accessible

↓

False
```

If connecting from outside AWS:

- VPN
- Bastion Host
- Systems Manager Session Manager

---

# Authentication Failures

Verify:

- Username
- Password
- IAM Authentication
- Secrets Manager

---

# IAM Authentication Issues

Verify:

- IAM enabled
- Database user configured
- IAM permissions
- Authentication token validity

---

# Database Login Failure

Possible causes:

- Invalid credentials
- Expired password
- Incorrect endpoint
- Wrong database name

---

# Storage Full

Monitor:

```text
FreeStorageSpace
```

Solutions:

- Increase storage
- Enable Storage Auto Scaling
- Remove unnecessary data

---

# High CPU Usage

Monitor:

```text
CPUUtilization
```

Possible causes:

- Missing indexes
- Long-running queries
- Full table scans
- High concurrency

---

# High Memory Usage

Review:

- Active connections
- Query cache
- Large transactions
- Parameter Groups

---

# TooManyConnections

Possible causes:

- Connection leaks
- Missing connection pooling
- Application bug

Recommended solution:

```text
Application

↓

RDS Proxy

↓

Amazon RDS
```

---

# Slow Queries

Use:

```text
Performance Insights
```

Review:

- Top SQL
- Wait events
- Execution plans

---

# Database Locked

Possible causes:

- Long-running transaction
- Deadlock
- Table lock

Investigate active sessions.

---

# Backup Failure

Verify:

- Backup retention enabled
- Storage availability
- Database status

---

# Snapshot Failure

Verify:

- Snapshot identifier
- Available storage
- Database state

---

# Restore Failure

Verify:

- Snapshot exists
- Region
- KMS permissions
- Storage limits

---

# Read Replica Lag

Monitor:

```text
Replica Lag
```

Common causes:

- Heavy writes
- Network latency
- Large transactions

---

# Read Replica Not Updating

Verify:

- Replication status
- Primary availability
- Storage
- Network connectivity

---

# Multi-AZ Failover Issues

Verify:

- Multi-AZ enabled
- Standby healthy
- DNS resolution

Applications should reconnect automatically.

---

# Pending Modifications

View:

```bash
aws rds describe-db-instances
```

Pending changes include:

- Storage
- Instance Class
- Parameter Groups

---

# Parameter Group Problems

Verify:

- Correct database family
- Supported parameters
- Reboot requirements

---

# Option Group Problems

Verify:

- Database engine
- Engine version
- Supported options

---

# Encryption Issues

Verify:

- AWS KMS Key
- IAM permissions
- Region

---

# Monitoring Problems

Check:

- CloudWatch
- Enhanced Monitoring
- Performance Insights

Ensure features are enabled.

---

# Event Notifications

View recent events.

```bash
aws rds describe-events
```

Review:

- Maintenance
- Failovers
- Backups
- Errors

---

# CloudWatch Metrics

Monitor:

- CPUUtilization
- DatabaseConnections
- ReadIOPS
- WriteIOPS
- ReadLatency
- WriteLatency
- FreeStorageSpace
- ReplicaLag

---

# Common Errors

## DBInstanceNotFound

Verify:

- Instance identifier
- Region
- AWS Account

---

## DBSnapshotNotFound

Verify:

- Snapshot name
- Region

---

## InvalidDBInstanceState

The requested operation is not allowed in the current instance state.

Wait until the database becomes:

```text
Available
```

---

## InsufficientStorage

Increase storage or enable Storage Auto Scaling.

---

## AccessDenied

Verify:

- IAM Policy
- KMS permissions
- Secrets Manager permissions

---

## Endpoint Not Reachable

Verify:

- Security Groups
- VPC Routing
- DNS
- Database status

---

## Authentication Failed

Verify:

- Username
- Password
- IAM token
- Database name

---

# Recovery Workflow

```text
Database Failure

↓

CloudWatch Alarm

↓

Investigate

↓

Restore Snapshot

↓

Validate

↓

Production
```

---

# Daily Operational Checklist

Review:

- Backup success
- Snapshot completion
- CPU utilization
- Storage utilization
- Database connections
- Slow queries
- Replica lag
- CloudWatch alarms

---

# Weekly Operational Checklist

Verify:

- Maintenance schedule
- Parameter Groups
- Security Groups
- IAM permissions
- Snapshot cleanup
- Storage growth
- Performance trends

---

# Production Best Practices

## Deploy Multi-AZ

Never deploy production databases in Single-AZ.

---

## Keep Databases Private

Deploy databases in private subnets.

---

## Enable Automated Backups

Maintain sufficient retention.

---

## Take Manual Snapshots

Before:

- Upgrades
- Schema migrations
- Major deployments

---

## Enable Monitoring

Use:

- CloudWatch
- Enhanced Monitoring
- Performance Insights

---

## Store Credentials Securely

Use:

```text
AWS Secrets Manager
```

Never hardcode credentials.

---

## Use RDS Proxy

Reduce connection overhead.

---

## Monitor Continuously

Configure CloudWatch alarms for:

- CPU
- Memory
- Storage
- Connections
- Replica Lag

---

## Test Disaster Recovery

Regularly verify:

- Snapshot restores
- Multi-AZ failover
- Read Replica promotion

---

# Real-World Workflow

```text
Application Error

↓

CloudWatch Alarm

↓

Describe DB Instance

↓

Review Metrics

↓

Review Logs

↓

Identify Root Cause

↓

Fix

↓

Validate

↓

Production
```

---

# Architecture Note

```text
Application
      │
      ▼
Amazon RDS Endpoint
      │
      ▼
Amazon RDS
      │
      ├── CloudWatch
      ├── Enhanced Monitoring
      ├── Performance Insights
      ├── Automated Backups
      └── Multi-AZ Standby
```

A production Amazon RDS deployment should be continuously monitored using CloudWatch, Enhanced Monitoring, and Performance Insights while relying on Multi-AZ, automated backups, and snapshots to ensure resilience and rapid recovery from failures.

---

# Interview Note

### Question

**How would you troubleshoot an application that suddenly cannot connect to an Amazon RDS database?**

### Answer

I would first verify that the DB instance is in the **Available** state using `describe-db-instances`. Next, I would confirm the application is using the correct RDS endpoint and that DNS resolution is working. I would then inspect Security Groups, subnet routing, and Network ACLs to ensure the database port is accessible. After verifying credentials or IAM database authentication, I would review CloudWatch metrics for CPU, memory, storage, and connection limits, check recent RDS events, and examine Performance Insights or database logs for underlying issues such as lock contention, high load, or failed authentication attempts.

---

# Key Takeaways

- Troubleshoot Amazon RDS from the application layer down to the database engine.
- Security Groups, endpoints, and networking are common causes of connectivity issues.
- CloudWatch, Enhanced Monitoring, and Performance Insights provide complementary monitoring capabilities.
- Automated backups, snapshots, and Multi-AZ deployments are essential for disaster recovery.
- RDS Proxy helps manage database connections efficiently.
- Regular operational reviews and disaster recovery testing improve production reliability.
- Combining monitoring, backups, security, and automation results in a resilient, production-ready database platform.