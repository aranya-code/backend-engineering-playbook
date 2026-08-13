# RDS Backups and Restore

Reliable backups and the ability to restore data quickly are the cornerstones of database disaster recovery. Amazon RDS manages backups automatically, providing automated continuous backups for Point-in-Time Recovery (PITR) and user-initiated manual snapshots.

Understanding backup types, retention rules, cross-region copying, and restore processes is critical for meeting target Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO).

---

# Automated Backups

Automated backups are enabled by default on RDS instances. They provide continuous protection by capturing database snapshots and transaction logs.

## Key Characteristics

- **Retention Period**: Configurable from **1 to 35 days** (set to `0` to disable automated backups, which also deletes existing automated backups and disables Point-in-Time Recovery).
- **Daily Snapshots**: RDS takes a full daily backup of your database storage volume during a user-defined **Backup Window**.
- **Transaction Logs**: RDS continuously archives database transaction logs (e.g., write-ahead logs in PostgreSQL, binary logs in MySQL) to Amazon S3 every **5 minutes**.
- **Performance Impact**: Automated backups are taken from the standby instance in Multi-AZ deployments, preventing performance impact on the primary instance. In Single-AZ deployments, brief I/O suspension (typically lasting a few seconds) can occur.
- **Dangling Backups**: Automated backups are **deleted when you delete the database instance**, unless you explicitly choose to retain automated backups during deletion.

## Point-in-Time Recovery (PITR)

Using the combination of daily snapshots and transaction logs, you can restore your database to any specific second within your retention period, up to the last 5 minutes.

```text
Last Full Snapshot (02:00 AM)  +  Transaction Logs (02:00 AM - 10:42 AM)
                         │
                         ▼
             Restored to 10:42:15 AM
```

---

# Manual Snapshots

Manual snapshots are full database backups initiated by the user.

- **Retention**: Manual snapshots are **retained indefinitely**. They are not deleted when you delete the parent database instance.
- **Copying**: Can be copied across AWS regions for disaster recovery.
- **Sharing**: Can be shared with other AWS accounts for development seeding, migration, or cross-account backup centralization.
- **Cross-Account Sharing Constraints**:
  - You **cannot share** snapshots encrypted with the default AWS-managed KMS key (`aws/rds`).
  - To share an encrypted snapshot, you must encrypt it with a **Customer Managed Key (CMK)**, share the key with the target account via key policy, and then share the snapshot.

---

# Snapshot Copy and KMS Key Transformation

When copying encrypted snapshots across accounts or regions, the snapshot must be re-encrypted (re-keyed) with a destination KMS key.

```text
Source Account                       Target Account (Destination Region)
┌──────────────────────┐             ┌──────────────────────────────────┐
│ Encrypted Snapshot   │             │                                  │
│ (Encrypted with      │             │                                  │
│  CMK Key A)          │             │                                  │
└──────────┬───────────┘             │                                  │
           │                         │                                  │
           │ Share snapshot          │                                  │
           ▼                         │                                  │
┌──────────────────────┐             │                                  │
│ Shared Snapshot      │────────────►│ Copy Snapshot (Re-encrypt)       │
│ (Accessible in B)    │             │ (Encrypt with CMK Key B)         │
└──────────────────────┘             └────────────────┬─────────────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │ Encrypted Copy   │
                                             │ (Restorable)     │
                                             └──────────────────┘
```

---

# The Restore Process

Restoring a database — whether from an automated backup or a manual snapshot — **always creates a new database instance**. You cannot restore over an existing database instance.

```text
Snapshot / PITR Source
       │
   Trigger Restore
       │
       ▼
1. RDS provisions a new EC2 host and new EBS storage volume
       │
       ▼
2. RDS restores snapshot data to the storage volume
       │
       ▼
3. RDS applies transaction logs (if performing PITR)
       │
       ▼
4. New database gets a new DNS Endpoint
       │
       ▼
5. Application cutover (update connection strings or DNS CNAME)
```

## Test-and-Cutover Strategy

Because restoring creates a new endpoint, you must update your applications to point to the new database. 

Use Route 53 CNAMEs to point to database endpoints. During a restore:
1. Provision the new restored database.
2. Validate data and run checks.
3. Update the Route 53 CNAME from the old instance to the new restored instance, avoiding application code deployments.

---

# Disaster Recovery Objectives: RPO and RTO

| Metric | Definition | RDS Capability |
|--------|------------|----------------|
| **Recovery Point Objective (RPO)** | The maximum acceptable data loss (time-based) | **5 minutes** (using transaction logs) or **0** (using active Multi-AZ replication). |
| **Recovery Time Objective (RTO)** | The maximum acceptable database downtime | **Minutes to Hours** (depends on the size of the database, storage allocation, and restoration speed). |

*Note: Restoring a multi-terabyte database can take hours. To achieve low RTO, rely on Multi-AZ failover or Aurora Backtrack rather than raw snapshot restoration.*

---

# Key Takeaways

- **Automated backups** enable Point-in-Time Recovery (PITR) to any second within 35 days, with a 5-minute RPO.
- **Manual snapshots** persist after database deletion and can be shared cross-account (requires CMK for encrypted snapshots).
- Restoring **always creates a new DB instance** with a new DNS endpoint.
- Backups are taken from the standby instance in Multi-AZ to eliminate performance overhead.
- Enable deletion protection in production to prevent accidental database deletion.

---
