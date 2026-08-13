# Security, Monitoring & Performance

> Learn how to secure, monitor, and optimize Amazon RDS databases using the AWS CLI. This chapter covers IAM authentication, encryption, Security Groups, CloudWatch monitoring, Enhanced Monitoring, Performance Insights, parameter tuning, logging, and production performance optimization.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Secure Amazon RDS databases
- Configure IAM database authentication
- Enable encryption
- Monitor database performance
- Configure Performance Insights
- Enable Enhanced Monitoring
- Optimize database performance
- Build secure production database environments

---

# Security Architecture

A secure Amazon RDS deployment consists of multiple security layers.

```text
Application

↓

IAM

↓

Security Group

↓

Amazon RDS

↓

Encryption
```

---

# Layers of Security

Amazon RDS security includes:

```text
Amazon RDS

│

├── IAM

├── VPC

├── Security Groups

├── Encryption

├── SSL/TLS

└── CloudTrail
```

---

# Security Groups

Security Groups control database access.

```text
Application

↓

Security Group

↓

Amazon RDS
```

Only trusted application servers should be allowed.

---

# Example Security Group Rule

Allow PostgreSQL:

```text
Port

↓

5432
```

Only from:

```text
Application Security Group
```

Never allow:

```text
0.0.0.0/0
```

for production databases.

---

# Public Access

Production recommendation:

```text
Publicly Accessible

↓

False
```

Applications should access databases through private networking.

---

# Encryption at Rest

Amazon RDS supports encryption using:

```text
AWS KMS
```

Encrypted resources include:

- Database storage
- Backups
- Snapshots
- Read Replicas

---

# Encryption Workflow

```text
Application

↓

Amazon RDS

↓

AWS KMS

↓

Encrypted Storage
```

---

# Create Encrypted Database

```bash
aws rds create-db-instance \
--storage-encrypted \
--kms-key-id alias/aws/rds
```

---

# Encryption in Transit

Connections should use:

```text
SSL/TLS
```

```text
Application

↓

TLS

↓

Amazon RDS
```

This protects data during transmission.

---

# IAM Database Authentication

Instead of passwords:

```text
Application

↓

IAM Authentication

↓

Amazon RDS
```

Supported engines include:

- MySQL
- PostgreSQL

---

# Enable IAM Authentication

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--enable-iam-database-authentication
```

---

# Benefits of IAM Authentication

- Temporary authentication tokens
- No stored passwords
- Centralized IAM management
- Better security

---

# Database Credentials

Avoid:

```text
Hardcoded Password
```

Prefer:

```text
AWS Secrets Manager
```

---

# Secrets Manager Integration

Architecture:

```text
Application

↓

Secrets Manager

↓

Amazon RDS
```

Applications retrieve credentials securely.

---

# CloudTrail

Amazon RDS API operations are logged in:

```text
AWS CloudTrail
```

Examples:

- Database creation
- Database deletion
- Snapshot creation
- Parameter modifications

---

# CloudWatch Integration

Amazon RDS publishes metrics to:

```text
Amazon CloudWatch
```

---

# Common CloudWatch Metrics

- CPUUtilization
- FreeStorageSpace
- DatabaseConnections
- ReadIOPS
- WriteIOPS
- ReadLatency
- WriteLatency
- FreeableMemory

---

# View CloudWatch Metrics

```text
Amazon RDS

↓

CloudWatch

↓

Metrics

↓

Dashboard
```

---

# Recommended Alarms

Configure alarms for:

```text
CPU > 80%
```

```text
Storage < 20%
```

```text
Connections > Threshold
```

```text
Replica Lag
```

---

# Enhanced Monitoring

Enhanced Monitoring provides operating system metrics.

```text
Amazon RDS

↓

Operating System

↓

CPU

↓

Memory

↓

Processes
```

---

# Enable Enhanced Monitoring

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--monitoring-interval 60
```

---

# Enhanced Monitoring Metrics

Includes:

- CPU utilization
- Memory usage
- Disk usage
- Process list
- Network activity

---

# Performance Insights

Performance Insights helps identify database bottlenecks.

Architecture:

```text
Application

↓

Database

↓

Performance Insights
```

---

# Enable Performance Insights

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--enable-performance-insights
```

---

# Performance Insights Displays

- Top SQL queries
- Wait events
- Database load
- Active sessions
- Query execution statistics

---

# Query Performance

Typical workflow:

```text
Slow Query

↓

Performance Insights

↓

Root Cause

↓

Optimization
```

---

# Parameter Groups

Parameter Groups optimize database behavior.

Examples:

- Shared buffers
- Work memory
- Logging
- Connection limits

---

# Database Logs

Amazon RDS supports logs such as:

- Error logs
- General logs
- Slow query logs
- Audit logs

---

# View Logs

```bash
aws rds describe-db-log-files \
--db-instance-identifier production-db
```

---

# Download Log File

```bash
aws rds download-db-log-file-portion \
--db-instance-identifier production-db \
--log-file-name error.log
```

---

# Connection Monitoring

Monitor:

```text
Application

↓

Database Connections

↓

Connection Pool
```

Excessive connections can degrade performance.

---

# Connection Pooling

Recommended tools:

- PgBouncer
- RDS Proxy

```text
Application

↓

RDS Proxy

↓

Amazon RDS
```

---

# Amazon RDS Proxy

Benefits:

- Connection pooling
- Improved scalability
- Faster failover
- Reduced database connections

---

# Storage Monitoring

Monitor:

- Free storage
- Storage growth
- IOPS
- Latency

Enable Storage Auto Scaling where appropriate.

---

# Common Errors

## TooManyConnections

Possible causes:

- Connection leaks
- Missing connection pool
- High traffic

---

## KMSKeyNotAccessible

Verify:

- KMS permissions
- Key exists
- Region

---

## IAM Authentication Failed

Verify:

- IAM permissions
- Database user
- Authentication enabled

---

## High CPU Utilization

Investigate:

- Slow queries
- Missing indexes
- Full table scans
- Long-running transactions

---

## Low Free Storage

Solutions:

- Increase storage
- Enable Storage Auto Scaling
- Remove unused data

---

# Production Best Practices

- Keep databases private.
- Enable encryption using AWS KMS.
- Enable SSL/TLS connections.
- Store credentials in AWS Secrets Manager.
- Enable Enhanced Monitoring.
- Enable Performance Insights.
- Configure CloudWatch alarms.
- Monitor slow queries.
- Use RDS Proxy for high-concurrency applications.
- Regularly review Parameter Groups.

---

# Real-World Workflow

```text
Deploy Database

↓

Enable Encryption

↓

Configure Security Groups

↓

Enable Monitoring

↓

Enable Performance Insights

↓

Configure Alarms

↓

Production
```

---

# Architecture Note

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
      ├── CloudWatch
      ├── Enhanced Monitoring
      ├── Performance Insights
      └── AWS KMS
```

A production-grade Amazon RDS deployment combines secure authentication, encryption, centralized monitoring, performance analysis, and connection pooling to deliver reliable, scalable, and secure database services.

---

# Interview Note

### Question

**What is the difference between CloudWatch, Enhanced Monitoring, and Performance Insights in Amazon RDS?**

### Answer

**CloudWatch** provides high-level database metrics such as CPU utilization, storage usage, IOPS, and connection counts. **Enhanced Monitoring** exposes operating system metrics like CPU, memory, processes, and disk activity from the underlying RDS instance. **Performance Insights** focuses on database performance by identifying slow SQL queries, wait events, database load, and execution bottlenecks, making it the primary tool for query-level performance tuning.

---

# Key Takeaways

- Security Groups restrict database network access.
- AWS KMS encrypts database storage, backups, and snapshots.
- IAM Authentication and AWS Secrets Manager improve credential security.
- CloudWatch monitors infrastructure metrics.
- Enhanced Monitoring provides operating system visibility.
- Performance Insights identifies SQL performance bottlenecks.
- RDS Proxy improves scalability by managing database connections efficiently.
```