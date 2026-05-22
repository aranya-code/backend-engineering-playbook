# RDS Multi-AZ

## Purpose

Provides high availability and disaster recovery.

---

## Key Features

- Synchronous replication
- Automatic failover
- Single DNS endpoint
- Standby DB in another AZ

---

## Important Note

Multi-AZ is NOT used for read scaling.

---

## Multi-AZ vs Read Replica

| Feature | Multi-AZ | Read Replica |
|---|---|---|
| Purpose | HA/DR | Read Scaling |
| Replication | Sync | Async |
| Automatic Failover | Yes | No |

---

## Personal Input

For production workloads, Multi-AZ is highly recommended.
