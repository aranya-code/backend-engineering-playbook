# Backup & Recovery

# Introduction

Backup and recovery strategies protect databases from accidental deletion, corruption, hardware failures, and disasters.

---

# Backup Types

## Full Backup
Copies the entire database.

## Incremental Backup
Stores only changes since the previous backup.

## Differential Backup
Stores changes since the last full backup.

---

# Recovery Objectives

## Recovery Point Objective (RPO)

Maximum acceptable data loss.

## Recovery Time Objective (RTO)

Maximum acceptable downtime before service restoration.

---

# AWS Services

- Amazon RDS Automated Backups
- Manual Snapshots
- Point-in-Time Recovery (PITR)
- AWS Backup

---

# Best Practices

- Automate backups.
- Test restoration regularly.
- Store backups across multiple Availability Zones or Regions.
- Define RPO and RTO before designing the solution.

---

# Interview Questions

1. Difference between backup and snapshot?
2. Explain RPO and RTO.
3. Why should backups be tested?

---

# Quick Revision

- Backup = Data protection
- Recovery = Restore service
- RPO = Data loss
- RTO = Downtime
