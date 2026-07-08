# Interview Questions: Amazon RDS and Aurora

This section provides detailed, senior-level interview questions and model answers focusing on Amazon RDS operations, Aurora architecture, and production database management on AWS.

---

# Amazon RDS Core Operations

## Q1: Your RDS instance is running out of storage at 3 AM. What happens, and how do you prevent this?

When an RDS instance runs out of storage, it transitions to a `storage-full` state and becomes read-only. All write operations fail, and the application begins throwing errors.

**Prevention with Storage Auto Scaling:**
- Enable Storage Auto Scaling on every RDS instance.
- RDS automatically increases storage when free space drops below 10% of allocated storage, the low-storage condition persists for 5+ minutes, and at least 6 hours have passed since the last modification.
- The increase is the greater of 10% of current storage or 10 GB.
- Always set a **Maximum Storage Threshold** to cap costs.

**Critical Detail**: Storage auto scaling only scales **upward**. You cannot reduce storage size once it has been increased. To reclaim storage, you must export data, create a new smaller instance, and import.

---

## Q2: Explain the difference between RDS Parameter Groups and Option Groups.

- **Parameter Groups** control database engine configuration settings (e.g., `max_connections`, `shared_buffers`, `innodb_buffer_pool_size`). They are equivalent to modifying `postgresql.conf` or `my.cnf`. Some parameters are dynamic (applied immediately), others are static (require a reboot).

- **Option Groups** enable optional database engine features that are not part of the core configuration (e.g., Oracle Enterprise Manager, SQL Server Audit, MySQL memcached plugin). Not all engines support option groups.

**Production Rule**: Never use the default parameter group. Default groups cannot be modified. Always create a custom parameter group from day one so you can tune settings as workload grows.

---

## Q3: Walk through the exact steps of an RDS Multi-AZ failover. What happens at each stage?

```text
1. Health Monitor detects primary failure (missed heartbeats / unreachable)
         │
         ▼
2. RDS marks primary as unhealthy (takes 30-60 seconds to confirm)
         │
         ▼
3. Standby instance is promoted to writable primary
         │
         ▼
4. DNS CNAME record updated to point to the new primary's IP address
         │
         ▼
5. Applications reconnect (after DNS TTL expires on client side)
         │
         ▼
6. RDS provisions a new standby in the old primary's AZ to restore HA
```

**Total failover time**: 60-120 seconds (can be reduced to ~30 seconds with RDS Proxy).

**Critical Detail**: The biggest delay is often **client-side DNS caching**. If the application or OS caches the old DNS record, connections will continue routing to the failed primary. Configure application-level DNS TTL to ≤30 seconds.

---

## Q4: How does RDS Proxy reduce failover time, and what is connection pinning?

**Failover Time Reduction:**
- Without Proxy: Client → DNS CNAME → Primary DB. During failover, the DNS record changes and clients must wait for DNS cache expiry + reconnect. Result: 60-120 second outage.
- With Proxy: Client → RDS Proxy (persistent connection) → Primary DB. During failover, the Proxy detects the new primary, redirects queries internally, and holds client connections in a queue. The client never disconnects. Result: ~30 second delay with no connection drops.

**Connection Pinning:**
Pinning occurs when the Proxy cannot safely multiplex a client session across pooled connections. The session is locked to a single backend connection, defeating the pooling benefit.

Common causes:
- Setting session-level variables (`SET timezone`, `SET search_path`)
- Creating temporary tables
- Preparing SQL statements
- Active advisory locks

**Mitigation**: Configure session-level settings in parameter groups instead of application code. Monitor `DatabaseConnectionsPinned` in CloudWatch.

---

## Q5: You need to encrypt an existing unencrypted production RDS database with zero data loss. Walk through the process.

You cannot enable encryption on a running unencrypted RDS instance. You must perform a snapshot-copy-restore migration:

```text
Step 1: Take a manual snapshot of the unencrypted instance
Step 2: Copy the snapshot, enabling encryption with a KMS CMK
Step 3: Restore the encrypted snapshot to a new RDS instance
Step 4: Verify data integrity on the new instance
Step 5: Update application connection strings (or Route 53 CNAME)
Step 6: Delete the old unencrypted instance
```

**Downtime Consideration**: There will be a brief cutover window during Step 5 where writes to the old instance are lost unless you quiesce the application. For true zero-downtime, set up a read replica from the old instance, promote it, then perform the encryption migration on the promoted replica while the old instance continues serving traffic.

---

# Amazon Aurora

## Q6: How does Aurora's storage architecture differ from standard RDS?

```text
Standard RDS:
┌──────────────┐          ┌──────────────┐
│ Primary DB   │          │ Standby DB   │
│ (EC2 + EBS)  │──sync──► │ (EC2 + EBS)  │
└──────────────┘          └──────────────┘
  Each instance has its own independent EBS volume.
  Replication is at the storage block level.

Aurora:
┌──────────────┐     ┌──────────────┐
│ Writer Node  │     │ Reader Node  │
│ (EC2 only)   │     │ (EC2 only)   │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ▼
┌────────────────────────────────────────┐
│       Shared Distributed Storage       │
│   (6 copies across 3 AZs, 10 GB chunks)│
│   Auto-scales up to 128 TiB           │
└────────────────────────────────────────┘
```

- Aurora writes data to 6 copies across 3 AZs. A write is acknowledged after 4 of 6 copies confirm (quorum write).
- Aurora can tolerate losing an entire AZ (2 copies) without losing write availability.
- Aurora can tolerate losing 2 AZs (4 copies) without losing read availability.
- Reader instances share the same storage volume — there is no replication lag from log shipping.

---

## Q7: What is Aurora Serverless v2 and when would you use it?

Aurora Serverless v2 automatically scales compute capacity (ACUs — Aurora Capacity Units) based on workload demand.

- **Scaling Range**: You define a minimum and maximum ACU. Aurora scales in increments of 0.5 ACU.
- **Scaling Speed**: Scales in seconds (not minutes like v1).
- **Use Cases**: 
  - Variable traffic workloads (e.g., development environments used during business hours only)
  - SaaS applications with unpredictable tenant activity
  - New applications where traffic patterns are unknown
- **When NOT to use**: Predictable, constant production workloads — provisioned instances with Reserved Instances are more cost-effective.

---

## Q8: Explain Aurora Global Database and how you perform a regional failover.

Aurora Global Database replicates data from a primary region to up to 5 secondary regions with typical replication lag under 1 second.

**Planned Failover (Switchover)**:
1. The primary region demotes itself.
2. A secondary region is promoted to become the new primary writer.
3. The old primary becomes a secondary.
4. Applications update their endpoints.
- **Use Case**: Relocating the primary closer to users, DR drills.
- **Data Loss**: Zero (RPO = 0).

**Unplanned Failover (Detach and Promote)**:
1. The secondary region is detached from the global cluster.
2. It becomes an independent, standalone Aurora cluster with write capability.
3. Applications in the secondary region reconnect to the new writer endpoint.
- **Use Case**: Primary region is completely unavailable.
- **Data Loss**: Potential data loss equal to the replication lag at the time of failure (typically <1 second).

---

## Q9: How does Aurora Backtrack differ from Point-in-Time Recovery?

| Feature | Aurora Backtrack | Point-in-Time Recovery (PITR) |
|---------|-----------------|-------------------------------|
| **Mechanism** | Rewinds the database in-place to a previous point in time | Restores a snapshot + transaction logs to a **new** database instance |
| **Speed** | Seconds (in-place rewind) | Minutes to hours (provisions new instance) |
| **New Instance** | No — same instance, same endpoint | Yes — new instance, new endpoint |
| **Data After Target** | All data after the target time is lost | Original instance remains unchanged |
| **Retention** | Configurable backtrack window (up to 72 hours) | Up to 35 days (backup retention) |
| **Use Case** | Quickly undo accidental `DELETE` or `DROP TABLE` | Disaster recovery, cloning for testing |

**Important**: Backtrack is only available for Aurora MySQL, not Aurora PostgreSQL.

---

## Q10: What is the difference between Aurora Writer Endpoint, Reader Endpoint, and Custom Endpoints?

- **Writer Endpoint (Cluster Endpoint)**: Always points to the current primary (writer) instance. Use for all write operations and consistency-critical reads.
- **Reader Endpoint**: Load-balances connections across all available reader instances. Use for read-heavy reporting and analytics queries.
- **Custom Endpoints**: User-defined endpoints that route to a subset of instances. Example: route analytical queries to larger reader instances while keeping lighter readers for the application tier.

```text
Application Layer
├── Writes ──────────────► Writer Endpoint ──► Primary Instance
├── App Reads ───────────► Reader Endpoint ──► Reader 1, Reader 2
└── Analytics Reads ─────► Custom Endpoint ──► Reader 3 (db.r6g.4xlarge)
```

---

# Operational Scenarios

## Q11: Your application team reports that database queries are suddenly 10x slower. How do you diagnose this on RDS?

**Diagnostic Steps:**

1. **Check CloudWatch Metrics**: Look at `CPUUtilization`, `FreeableMemory`, `ReadIOPS`, `WriteIOPS`, `ReadLatency`, `WriteLatency`. Identify which resource is saturated.

2. **Check Performance Insights**: Open PI and look at the **DB Load** chart. If AAS (Average Active Sessions) exceeds the Max vCPU line, the database is saturated. Filter by Top SQL to find the query causing the load.

3. **Check for Locks**: Filter PI by Wait State. If `Lock:transactionrow` or `Lock:tuple` is dominant, queries are blocking each other. Identify the blocking PID and the locked table.

4. **Check `ReplicaLag`**: If the application reads from a read replica, high replication lag can cause stale data and force retries against the primary, compounding the problem.

5. **Check Recent Deployments**: Did the application team deploy a new code version? A new query without an index can cause a full table scan that wasn't present before.

**Resolution Path**: Run `EXPLAIN ANALYZE` on the top offending query. If it shows a sequential scan, add the appropriate index. If it shows lock waits, investigate and resolve the blocking transaction.

---

## Q12: How do you perform a major version upgrade of PostgreSQL on RDS with minimal downtime?

**Blue-Green Deployment Approach (Recommended):**

```text
1. Create a Blue-Green deployment from the production (Blue) instance
         │
         ▼
2. RDS provisions a Green environment (new engine version)
   and sets up logical replication from Blue → Green
         │
         ▼
3. Green catches up and stays in sync (replication lag → 0)
         │
         ▼
4. Trigger switchover: RDS swaps endpoints
   - Blue endpoint now points to Green
   - Application reconnects automatically
         │
         ▼
5. Verify application health on Green
         │
         ▼
6. Delete old Blue environment
```

**Downtime**: Typically under 1 minute during the switchover phase.

**Fallback**: If issues are detected on Green, you can roll back by switching endpoints back to Blue (within the rollback window).

---

# Key Takeaways

- Storage auto scaling only scales up. Always set a maximum threshold to cap unexpected costs.
- Never use default parameter groups — they cannot be modified.
- Multi-AZ failover takes 60-120 seconds; RDS Proxy reduces this to ~30 seconds.
- Aurora's shared distributed storage eliminates traditional replication lag between writer and reader instances.
- Aurora Backtrack rewinds in-place (seconds), while PITR creates a new instance (minutes-hours).
- Use Blue-Green deployments for major version upgrades to minimize downtime.

---
