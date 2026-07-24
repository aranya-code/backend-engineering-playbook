# Backup & Restore

## Overview

Although Redis is an in-memory database, production systems often store valuable business data such as:

- User sessions
- Shopping carts
- Cached API responses
- Rate limiting counters
- Distributed locks
- Job queues
- Leaderboards
- Financial transaction states
- Feature flags

Losing this data can result in service disruption, revenue loss, or data inconsistency.

A robust backup and restore strategy ensures that Redis can recover from:

- Hardware failures
- Disk failures
- Accidental deletion
- Software bugs
- Human errors
- Ransomware
- Cloud infrastructure failures
- Regional disasters

Backup and disaster recovery should be treated as part of every production deployment.

---

# Backup vs Persistence

Many engineers confuse persistence with backups.

They are different.

| Persistence | Backup |
|-------------|---------|
| Keeps Redis durable during normal operations | Protects against catastrophic failures |
| Uses RDB or AOF | Creates independent copies |
| Stored on the Redis server | Stored elsewhere |
| Helps recover after restart | Helps recover after data loss |

Example

```
Redis

↓

RDB File
```

is **not** a backup.

A backup is

```
Redis

↓

RDB

↓

Cloud Storage

↓

Restore Later
```

---

# Disaster Recovery Architecture

```
                Production Redis

                       │

          ┌────────────┴────────────┐

          ▼                         ▼

      RDB Snapshot            AOF File

          │                         │

          └────────────┬────────────┘

                       ▼

                 Backup Server

                       │

                Cloud Storage

                       │

                Disaster Recovery
```

---

# Recovery Objectives

Every production system should define:

## Recovery Time Objective (RTO)

```
Failure

↓

Recovery Time
```

Measures

> How quickly Redis must be restored.

Example

```
15 Minutes
```

---

## Recovery Point Objective (RPO)

```
Failure

↓

Maximum Acceptable Data Loss
```

Example

```
1 Minute
```

Lower RPO requires more frequent persistence and backups.

---

# Backup Strategies

Common strategies include:

- RDB snapshots
- AOF backups
- Hybrid persistence
- Cloud snapshots
- Replica backups
- Filesystem snapshots

---

# RDB Backups

Redis periodically creates snapshots.

```
Redis

↓

dump.rdb

↓

Backup
```

Advantages

- Small files
- Fast restore
- Easy archival

Disadvantages

- Possible data loss between snapshots

---

# AOF Backups

The Append Only File records every write.

```
SET

↓

Logged

↓

appendonly.aof
```

Advantages

- Better durability
- Smaller RPO

Disadvantages

- Larger backup files
- Slower restore

---

# Hybrid Persistence

Modern Redis supports both.

```
Redis

↓

RDB

+

AOF

↓

Maximum Safety
```

Recommended for production.

---

# Backup Workflow

```
Redis

↓

Snapshot

↓

Compress

↓

Encrypt

↓

Upload

↓

Cloud Storage
```

Automation is essential.

---

# Backup Frequency

Different workloads require different schedules.

| Workload | Suggested Frequency |
|----------|--------------------|
| Cache Only | Daily |
| Sessions | Hourly |
| Financial Data | Every Few Minutes |
| Critical Messaging | Continuous (AOF) |

---

# Automated Backups

Production backups should never rely on manual execution.

Typical workflow

```
Scheduler

↓

Redis SAVE

↓

Upload Backup

↓

Verify

↓

Notify
```

---

# Backup Storage

Never store backups only on the Redis server.

Bad

```
Redis

↓

Backup

↓

Same Disk
```

Disk failure destroys both.

Better

```
Redis

↓

Backup

↓

Remote Storage
```

---

# Cloud Backup Storage

Common destinations

- Amazon S3
- Azure Blob Storage
- Google Cloud Storage
- Network Attached Storage (NAS)

Architecture

```
Redis

↓

Backup Server

↓

Cloud Storage

↓

Long-Term Archive
```

---

# Backup Retention Policy

Avoid keeping only the latest backup.

Example

```
Daily

↓

7 Days

Weekly

↓

4 Weeks

Monthly

↓

12 Months
```

This allows recovery from delayed data corruption.

---

# Backup Verification

A backup is useless if it cannot be restored.

Workflow

```
Backup Created

↓

Restore Test

↓

Validation

↓

Success
```

Regular verification is mandatory.

---

# Backup Compression

Large datasets consume storage.

```
RDB

↓

Compression

↓

Smaller File
```

Benefits

- Lower storage costs
- Faster transfer
- Reduced bandwidth

---

# Backup Encryption

Backups often contain sensitive information.

Protect them.

```
Backup

↓

Encryption

↓

Cloud Storage
```

Never store unencrypted backups in public locations.

---

# Restore Process

Typical restore workflow

```
Failure

↓

Stop Redis

↓

Restore Backup

↓

Start Redis

↓

Validation

↓

Application Online
```

---

# Restoring an RDB Backup

Steps

1. Stop Redis.
2. Replace the existing `dump.rdb`.
3. Start Redis.
4. Redis loads the snapshot automatically.

Architecture

```
Old dump.rdb

↓

Replace

↓

New dump.rdb

↓

Redis Startup
```

---

# Restoring an AOF Backup

Workflow

```
appendonly.aof

↓

Redis Startup

↓

Replay Commands

↓

Database Rebuilt
```

Restore may take longer than RDB for very large datasets.

---

# Restoring to Another Server

Useful during disaster recovery.

```
Backup

↓

New Server

↓

Restore

↓

Applications Reconnect
```

---

# Point-in-Time Recovery

Using AOF

```
Command History

↓

Replay Until

↓

Desired Time
```

Useful after accidental deletions.

---

# Backup Validation

After restoration verify:

- Key count
- Memory usage
- Application connectivity
- Data integrity
- Replication status

Never assume a restore succeeded.

---

# Replica-Based Backups

Instead of backing up the primary

```
Primary

↓

Replica

↓

Backup
```

Advantages

- Lower impact on production
- Reduced I/O on primary

---

# Kubernetes Backup

```
Redis Pod

↓

Persistent Volume

↓

Snapshot

↓

Object Storage
```

Use Kubernetes-native snapshot capabilities when available.

---

# AWS Backup Architecture

```
Amazon ElastiCache

↓

Snapshot

↓

AWS Backup

↓

S3

↓

Cross-Region Copy
```

Supports disaster recovery across AWS Regions.

---

# Multi-Region Backup

```
Primary Region

↓

Backup

↓

Secondary Region

↓

Restore
```

Protects against regional outages.

---

# Disaster Recovery Drill

Backups should be tested regularly.

```
Restore Backup

↓

Run Application

↓

Verify Data

↓

Document Results
```

Practice reduces recovery time during real incidents.

---

# Monitoring Backups

Monitor

- Backup duration
- Backup size
- Failed backups
- Restore success
- Snapshot age
- Storage utilization

Alerts should be generated for backup failures.

---

# Common Backup Mistakes

## Assuming Persistence Is a Backup

Persistence helps after restarts.

It does not protect against:

- Accidental deletion
- Data corruption
- Ransomware
- Infrastructure failure

---

## Storing Backups on the Same Server

```
Disk Failure

↓

Redis Lost

↓

Backup Lost
```

Always use external storage.

---

## Never Testing Restores

Many organizations discover broken backups only during an outage.

Regular restore testing is essential.

---

## Keeping Only One Backup

Corrupted backups overwrite healthy ones.

Maintain multiple restore points.

---

## Unencrypted Backups

Sensitive customer data should always be encrypted before leaving production infrastructure.

---

# Production Backup Checklist

Before deploying to production, verify:

- Automated backup schedule configured
- Backup encryption enabled
- Off-site storage configured
- Retention policy documented
- Restore procedures documented
- Restore tests performed
- Backup monitoring enabled
- Recovery objectives (RTO/RPO) defined

---

# Best Practices

- Automate every backup process.
- Combine RDB and AOF for improved durability.
- Store backups outside the Redis host.
- Encrypt backup files before archival.
- Keep multiple backup generations.
- Test restore procedures regularly.
- Define RTO and RPO based on business requirements.
- Document disaster recovery procedures and responsibilities.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Snapshot Frequency | Balance durability with performance |
| Compression | Reduce storage and transfer costs |
| Encryption | Protect sensitive data |
| Replica Backups | Reduce load on the primary |
| Restore Testing | Ensure backup reliability |
| Remote Storage | Improve disaster resilience |

---

# Production Considerations

For production environments:

- Integrate backup workflows into CI/CD and infrastructure automation.
- Perform backups during periods of lower system activity when possible.
- Monitor backup success rates and investigate failures immediately.
- Replicate backups across multiple geographic locations for critical workloads.
- Review retention policies regularly to meet business and compliance requirements.
- Conduct periodic disaster recovery exercises involving both infrastructure and application teams.

---

# Summary

Backups are a fundamental component of Redis production operations. While persistence protects against routine restarts, backups provide protection against catastrophic failures, accidental data loss, and disaster scenarios. A mature backup strategy includes automated snapshots, secure off-site storage, encryption, retention policies, restore testing, and clearly defined recovery objectives. Reliable backups ensure Redis can be restored quickly with minimal data loss when unexpected events occur.

---

# Key Takeaways

- Persistence and backups serve different purposes.
- Define clear RTO and RPO targets for your Redis deployment.
- Use automated RDB and/or AOF backups based on workload requirements.
- Store backups in secure, remote locations with encryption enabled.
- Maintain multiple backup generations using a retention policy.
- Validate backups by performing regular restore tests.
- Use replica-based backups to reduce impact on production.
- Treat backup and disaster recovery as continuous operational processes rather than one-time tasks.