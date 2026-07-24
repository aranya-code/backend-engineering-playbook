# Persistence Failures

## Overview

Redis is primarily an **in-memory database**, but persistence allows data to survive process restarts, crashes, and server failures.

Redis supports two persistence mechanisms:

- **RDB (Redis Database Snapshot)**
- **AOF (Append Only File)**

Production environments often enable one or both.

When persistence fails, Redis may experience:

- Data loss
- Startup failures
- Failed backups
- Increased latency
- Full disks
- Replication failures

Understanding persistence failures is critical for operating Redis safely in production.

---

# Persistence Architecture

```
                  Client Writes
                        │
                        ▼
                 +---------------+
                 |     Redis     |
                 +---------------+
                    │         │
        Snapshot    │         │ Append
        (RDB)        │         │ Only
                    ▼         ▼
             dump.rdb    appendonly.aof
```

---

# Persistence Workflow

```
Application

        │

        ▼

Write Data

        │

        ▼

Redis Memory

        │

 ┌──────┴─────────┐

 │                │

RDB Snapshot    AOF Append

 │                │

 ▼                ▼

Disk           Disk
```

---

# Common Persistence Problems

| Problem | Symptoms |
|----------|----------|
| RDB snapshot failed | Backup missing |
| AOF corrupted | Redis won't start |
| Disk full | Persistence disabled |
| Slow disk | Latency spikes |
| Background save failure | MISCONF errors |
| AOF rewrite failure | Growing disk usage |
| Corrupted persistence file | Startup failure |

---

# Step 1 — Check Persistence Status

Run

```bash
redis-cli INFO persistence
```

Example

```text
loading:0

rdb_bgsave_in_progress:0

aof_enabled:1
```

Important fields include:

- loading
- rdb_last_bgsave_status
- aof_enabled
- aof_last_write_status
- aof_last_bgrewrite_status

---

# RDB Snapshot Failure

Check

```text
rdb_last_bgsave_status
```

Healthy

```text
ok
```

Failure

```text
err
```

---

# AOF Status

Check

```text
aof_last_write_status
```

Expected

```text
ok
```

Any other value requires investigation.

---

# Background Save Failure

Typical error

```text
MISCONF Redis is configured to save RDB snapshots
```

Redis may reject writes if snapshots repeatedly fail.

---

# Verify Disk Space

Check

```bash
df -h
```

Example

```
Filesystem

100% Used
```

A full disk is one of the most common causes of persistence failures.

---

# Verify Disk Performance

Monitor

```bash
iostat
```

Look for

- High utilization
- Long write latency
- Queue buildup

Slow storage affects snapshot creation.

---

# RDB Corruption

Example startup log

```text
Short read or CRC error
```

Verify

```bash
redis-check-rdb dump.rdb
```

If corruption exists, restore from backup whenever possible.

---

# AOF Corruption

Example

```text
Bad file format
```

Repair

```bash
redis-check-aof --fix appendonly.aof
```

Always create a backup before attempting repairs.

---

# AOF Rewrite

Redis periodically rewrites the AOF file.

```
Old AOF

↓

Rewrite

↓

Compact AOF
```

Monitor

```text
aof_rewrite_in_progress
```

---

# Fork Failures

Persistence uses

```
Fork

↓

Child Process

↓

Snapshot
```

Insufficient memory can prevent the fork from succeeding.

Monitor

```bash
free -h
```

---

# Copy-on-Write

During snapshots

```
Parent

↓

Fork

↓

Child

↓

Copy-on-Write
```

Additional memory is temporarily required.

Always reserve free RAM for persistence.

---

# Loading State

After restart

```
Redis

↓

Loading RDB/AOF

↓

Ready
```

Check

```text
loading
```

Applications should wait until loading completes.

---

# Docker Considerations

Incorrect

```
Container

↓

No Volume

↓

Persistence Lost
```

Correct

```
Redis

↓

Persistent Volume

↓

Host Storage
```

---

# Kubernetes Considerations

Use

- PersistentVolume
- PersistentVolumeClaim
- StatefulSet

Avoid storing persistence data on ephemeral container filesystems.

---

# AWS ElastiCache

Managed Redis automatically handles many persistence operations.

Monitor CloudWatch metrics for:

- Snapshot failures
- Storage usage
- Backup completion
- Maintenance events

---

# Useful Commands

Persistence information

```bash
INFO persistence
```

Configuration

```bash
CONFIG GET save
```

AOF

```bash
CONFIG GET appendonly
```

Disk usage

```bash
df -h
```

RDB validation

```bash
redis-check-rdb dump.rdb
```

AOF validation

```bash
redis-check-aof appendonly.aof
```

---

# Diagnostic Workflow

```
Persistence Failure

        │

        ▼

INFO persistence

        │

        ▼

RDB or AOF?

        │

 ┌──────┴────────┐

 │               │

RDB            AOF

 │               │

Check Save    Check Write

 │               │

 ▼               ▼

Disk         Rewrite

 │               │

 ▼               ▼

Corruption    Corruption

 │               │

 ▼               ▼

Restore       Repair
```

---

# Common Mistakes

## Running Without Backups

Persistence is not a substitute for backups.

Maintain external backup copies.

---

## Ignoring Disk Capacity

Snapshots require free disk space.

Monitor storage utilization continuously.

---

## Disabling Persistence

Turning off persistence to solve operational issues risks permanent data loss.

---

## No Persistent Volume

Containers without persistent storage lose data after restart.

---

## Ignoring Background Save Errors

Repeated snapshot failures usually indicate infrastructure problems.

Investigate immediately.

---

# Best Practices

- Enable RDB, AOF, or both based on workload requirements.
- Monitor persistence health continuously.
- Validate backups regularly.
- Reserve sufficient RAM for Copy-on-Write.
- Use SSD storage for persistence files.
- Store persistence data on reliable persistent volumes.
- Alert on failed snapshots or AOF writes.
- Test backup restoration procedures regularly.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Disk | Use SSDs |
| Memory | Reserve RAM for forks |
| Monitoring | Watch persistence metrics |
| AOF | Monitor rewrite frequency |
| RDB | Verify snapshot success |
| Backups | Test restores regularly |

---

# Production Considerations

For production deployments:

- Monitor `INFO persistence` continuously.
- Configure alerts for failed RDB snapshots and AOF writes.
- Ensure sufficient free disk space and memory before persistence operations.
- Keep persistence files on reliable storage with regular backups.
- Validate disaster recovery by periodically restoring backups in a staging environment.
- Use persistent volumes for containerized Redis deployments.
- Document backup, restore, and recovery procedures as part of your operational runbooks.

---

# Summary

Redis persistence protects in-memory data against process restarts and infrastructure failures. Most persistence issues are caused by insufficient disk space, storage performance problems, memory constraints during snapshot creation, or corrupted persistence files. By monitoring persistence health, validating backups, and maintaining reliable storage, teams can significantly reduce the risk of data loss in production.

---

# Key Takeaways

- Redis supports both **RDB** and **AOF** persistence mechanisms.
- Use `INFO persistence` to monitor persistence health.
- Regularly validate RDB and AOF files using Redis tooling.
- Ensure sufficient disk space and memory for snapshot operations.
- Use persistent storage for Docker and Kubernetes deployments.
- Monitor snapshot and AOF rewrite failures proactively.
- Test backup restoration procedures—not just backup creation.
- Persistence is essential for durability but should always be complemented by a robust backup strategy.