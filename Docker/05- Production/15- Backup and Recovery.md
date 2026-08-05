# Backup and Recovery

## Overview

Containers are designed to be disposable, but application data is not. A production deployment must have a reliable backup and recovery strategy to protect against hardware failures, software bugs, accidental deletions, ransomware, and operational mistakes.

Backups ensure data can be restored after a failure, while recovery procedures define how quickly services can return to normal operation.

A good backup strategy focuses on:

- Data protection
- Business continuity
- Disaster recovery
- Fast restoration
- Regular testing

---

# Why Backup Matters

Without backups

```text
Database Failure

↓

Data Lost

↓

Service Unavailable

↓

Business Impact
```

With backups

```text
Database Failure

↓

Restore Backup

↓

Application Running

↓

Minimal Downtime
```

---

# What Should Be Backed Up?

Typical production backups include:

- Databases
- Docker volumes
- User uploads
- Configuration files
- Environment files
- SSL certificates
- Deployment scripts
- Infrastructure configuration

Application source code should already be stored in version control.

---

# Backup Architecture

```text
Application

↓

Docker Volume

↓

Backup Process

↓

Backup Storage

↓

Recovery
```

---

# Docker Volumes

Most production data is stored in Docker volumes.

```text
Container

↓

Docker Volume

↓

Persistent Storage
```

Backing up the volume protects application data.

---

# Backup Workflow

```text
Running Application

↓

Backup Job

↓

Archive

↓

Remote Storage

↓

Retention
```

---

# Database Backups

Database backups are the highest priority.

Example PostgreSQL

```bash
pg_dump \
    -U postgres \
    appdb \
    > backup.sql
```

Example MySQL

```bash
mysqldump \
    -u root \
    -p appdb \
    > backup.sql
```

These backups capture logical database contents.

---

# Volume Backup Example

Create a compressed archive.

```bash
docker run \
    --rm \
    -v postgres_data:/volume \
    -v $(pwd):/backup \
    alpine \
    tar czf /backup/postgres.tar.gz \
    /volume
```

Workflow

```text
Docker Volume

↓

Compressed Archive

↓

Backup Storage
```

---

# Restore Example

Restore a volume.

```bash
docker run \
    --rm \
    -v postgres_data:/volume \
    -v $(pwd):/backup \
    alpine \
    tar xzf /backup/postgres.tar.gz \
    -C /
```

After restoration

```text
Volume

↓

Container Starts

↓

Application Ready
```

---

# Backup Frequency

Different data requires different schedules.

| Data | Typical Frequency |
|------|-------------------|
| Databases | Daily or more frequently depending on business requirements |
| User uploads | Daily |
| Configuration | After changes |
| SSL certificates | After renewal |
| Docker volumes | Regularly based on business requirements |

Backup frequency should match the acceptable amount of potential data loss.

---

# Full vs Incremental Backups

| Full Backup | Incremental Backup |
|-------------|-------------------|
| Copies all data | Copies only changes |
| Larger | Smaller |
| Slower | Faster |
| Easier restoration | More complex restoration |

Many organizations combine both approaches.

---

# Backup Storage

Never store backups only on the production server.

Better architecture

```text
Production Server

↓

Backup

↓

Remote Storage

↓

Secondary Region
```

Examples include:

- Network storage
- Cloud object storage
- Backup servers
- Disaster recovery sites

---

# Backup Retention

Typical strategy

```text
Daily

↓

Weekly

↓

Monthly

↓

Yearly
```

Retention policies should follow business and regulatory requirements.

---

# Recovery Workflow

```text
Failure

↓

Identify Problem

↓

Select Backup

↓

Restore Data

↓

Verify

↓

Application Online
```

Recovery procedures should be documented before an incident occurs.

---

# Recovery Time Objective (RTO)

RTO measures:

```text
Failure

↓

Recovery

↓

Application Available
```

It defines how quickly a service should be restored after an outage.

Example

```text
RTO = 30 Minutes
```

---

# Recovery Point Objective (RPO)

RPO measures acceptable data loss.

```text
Latest Backup

↓

Failure

↓

Recovered Data
```

Example

```text
RPO = 15 Minutes
```

This means losing up to 15 minutes of recent data is considered acceptable.

---

# Disaster Recovery

A disaster recovery plan includes:

- Backup locations
- Restoration procedures
- Infrastructure recovery
- Communication plan
- Verification steps

Example

```text
Server Failure

↓

Provision New Server

↓

Restore Backup

↓

Deploy Containers

↓

Production Restored
```

---

# Verify Backups

A backup is only valuable if it can be restored.

Testing should include:

- Restore database
- Restore Docker volumes
- Start application
- Verify data
- Validate application functionality

---

# Automation

Backups should be automated.

```text
Scheduler

↓

Backup Script

↓

Archive

↓

Cloud Storage

↓

Notification
```

Manual backups are prone to being forgotten or performed inconsistently.

---

# Monitoring Backup Jobs

Monitor:

- Successful backups
- Failed backups
- Backup duration
- Storage usage
- Restore test results

Alerts should be generated for failed backup jobs.

---

# Backup Lifecycle

```text
Create Data

↓

Backup

↓

Store

↓

Retain

↓

Restore

↓

Verify
```

---

# Common Mistakes

## No Backups

Without backups, recovery from data loss may be impossible.

---

## Keeping Backups on the Same Server

Hardware failures can destroy both production data and backups.

Always store backups separately.

---

## Never Testing Restores

An untested backup should not be assumed to be usable.

Regular restoration testing is essential.

---

## Backing Up Containers Instead of Data

Containers should be recreated from images.

Back up the data, not the running container.

---

## No Retention Policy

Without retention, backups either consume excessive storage or disappear too soon.

---

# Production Checklist

Before deployment:

- Database backup configured
- Docker volumes backed up
- Configuration backed up
- Backup automation enabled
- Remote storage configured
- Retention policy defined
- Restore process documented
- Recovery tested
- Backup monitoring enabled
- Alerts configured

---

# Best Practices

- Back up persistent data rather than containers.
- Automate backup jobs.
- Store backups in a separate location.
- Encrypt sensitive backup data where appropriate.
- Define clear retention policies.
- Test recovery procedures regularly.
- Monitor backup success and failures.
- Document disaster recovery procedures.

---

# Key Takeaways

- Containers are disposable, but application data is not.
- A reliable backup strategy protects against hardware failures, human error, and software issues.
- Docker volumes and databases should be backed up regularly using automated processes.
- Recovery procedures should be documented and tested before they are needed.
- Backup and recovery planning is a critical part of operating reliable production Docker environments.