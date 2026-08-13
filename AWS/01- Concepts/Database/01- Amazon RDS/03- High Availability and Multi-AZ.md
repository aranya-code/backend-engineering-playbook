# High Availability and Multi-AZ

High availability (HA) is a critical requirement for production databases. In Amazon RDS, HA is achieved through **Multi-AZ** deployments. Multi-AZ protects your database against hardware failure, storage failure, Availability Zone outages, and database maintenance downtime by maintaining an exact standby replica in a separate Availability Zone.

Understanding the difference between Multi-AZ Instance deployments and Multi-AZ Cluster deployments, the failover process, and the migration path is essential for senior DevOps engineers.

---

# Multi-AZ DB Instance Deployments (Active-Passive)

A Multi-AZ DB Instance deployment provisions a primary DB instance and an exact standby instance in a different Availability Zone.

```text
       Client Application
               │
               │ (Connects to DB DNS Endpoint)
               ▼
┌───────────────────────────────┐
│     Route 53 DNS CNAME        │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Primary DB Instance (AZ-1)   │
│  (Active - Processes Queries) │
└──────────────┬────────────────┘
               │
               │ Synchronous Replication (EBS Level)
               ▼
┌───────────────────────────────┐
│  Standby DB Instance (AZ-2)   │
│  (Passive - Ready for HA)     │
└───────────────────────────────┘
```

## Key Characteristics

- **Synchronous Replication**: Replication occurs at the storage (EBS) level. When data is written to the primary, it is written to the standby storage synchronously before returning a commit confirmation to the application. This ensures **zero data loss** (RPO = 0) in the event of a failover.
- **Passive Standby**: The standby instance cannot accept connections or read queries. It exists purely as a failover target.
- **Backups**: To prevent performance degradation on the primary, automated backups and snapshots are taken from the **standby instance** instead of the primary.
- **DNS Endpoint**: Applications connect to a single, consistent DNS endpoint (CNAME). During failover, RDS updates the CNAME to point to the standby instance.

---

# The Failover Process

RDS automatically detects failures and initiates failover. The process typically takes **60 to 120 seconds** (can be reduced to under 30 seconds with RDS Proxy or short client connection timeouts).

## Triggers for Failover

- Loss of network connectivity to the primary instance.
- Storage failure on the primary volume.
- Host physical hardware failure.
- AZ-wide outage.
- Manual failover (reboot with failover triggered by the user).
- Minor engine patching or database maintenance (the standby is patched first, then RDS performs a failover, and then patches the old primary, minimizing downtime).

## Steps of an Automated Failover

```text
Primary Instance Fails
       │
       ▼
1. RDS Health Monitor detects failure (missed heartbeats)
       │
       ▼
2. RDS promotes Standby Instance (AZ-2) to Primary (Writable)
       │
       ▼
3. RDS updates the DB DNS CNAME to point to AZ-2 IP address
       │
       ▼
4. Applications reconnect (upon DNS cache TTL expiry)
       │
       ▼
5. RDS provisions a new Standby Instance in AZ-1 to restore HA
```

*Note: Application client-side DNS caching can delay failover recovery. Ensure client-side DNS TTL is configured to a very low value (e.g., less than 30 seconds).*

---

# Multi-AZ DB Cluster Deployments (Active-Two Passives)

Introduced to provide lower write latency and readable standby instances. A Multi-AZ DB Cluster deploys one writer instance and two reader instances across three Availability Zones.

- **Storage Layer Replication**: Uses semi-synchronous replication at the database engine level, optimized for lower write latency compared to storage-level replication.
- **Readable Standbys**: The two standby instances are **readable**. They can accept read queries using reader endpoints, providing both high availability and read scalability.
- **Faster Failover**: Typically fails over in **under 35 seconds** because the standby instances are already running and active, and transaction log recovery is optimized.

---

# Single-AZ to Multi-AZ Conversion Path

Converting a Single-AZ database to a Multi-AZ database can be done online with minimal impact on the active database.

```text
Modify DB: Enable Multi-AZ
       │
       ▼
1. RDS takes a snapshot of the primary database (no downtime)
       │
       ▼
2. RDS restores the snapshot to a new instance in a different AZ
       │
       ▼
3. RDS configures synchronous replication between Primary and Standby
       │
       ▼
4. Replication catches up, state changes to "Available" (Multi-AZ active)
```

*Warning: During step 1, S3 snapshot upload might cause brief I/O suspension or performance degradation on write-heavy databases. Schedule this change during off-peak hours.*

---

# Multi-AZ vs. Read Replicas (HA vs. Scaling)

This is one of the most critical comparison topics in database design.

| Feature | Multi-AZ Deployment | Read Replicas |
|---------|---------------------|---------------|
| **Primary Purpose** | High Availability & Disaster Recovery | Read Scaling & Reporting |
| **Replication Type**| Synchronous | Asynchronous |
| **Active/Passive** | Passive (Standby is not accessible) | Active (Writable primary, readable replicas) |
| **Failover** | Automatic (handled by RDS) | Manual promotion |
| **Target Audience** | Critical production databases | Read-heavy applications |
| **Cost** | Doubles DB instance & storage cost | Incremental per replica instance |
| **Impact on Primary**| Slight write latency overhead | Zero write overhead |
| **Backups** | Backups taken from standby | Backups can be disabled on replicas |

---

# Key Takeaways

- **Multi-AZ** provides synchronous replication, automatic failover, and zero data loss (RPO = 0) for high availability.
- Standby instances in standard Multi-AZ deployments are **passive** and cannot be read from.
- **Multi-AZ DB Clusters** provide readable standbys and lower write latency across three AZs.
- Failover works by updating the **DNS CNAME** record — configure applications with low DNS caching TTL.
- Convert from Single-AZ to Multi-AZ online; RDS handles snapshotting, restoring, and syncing automatically.

---
