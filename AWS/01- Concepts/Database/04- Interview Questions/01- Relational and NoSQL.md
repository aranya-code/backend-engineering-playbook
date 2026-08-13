# Interview Questions: Relational and NoSQL

This section provides detailed, senior-level interview questions and model answers focusing on relational databases, NoSQL systems, and their deployment on AWS.

---

# Core Database Models

## Q1: SQL vs. NoSQL: How do you choose between them for a production system?

The decision depends on data structure, transaction integrity, scaling patterns, and query complexity.

```text
                  Database Selection Flow:
                  
               Are transactions ACID critical?
             (e.g., Ledger, Payments, Orders)
                       ├── YES ──► Choose SQL (RDS / Aurora)
                       └── NO
                            │
               Is schema flexible or high-throughput?
                (e.g., IoT, Catalog, User Feeds)
                       ├── YES ──► Choose NoSQL (DynamoDB / DocumentDB)
                       └── NO  ──► Evaluate SQL (Lower operational overhead)
```

- **Choose Relational (SQL) When**:
  - You require strong ACID compliance and transaction integrity (e.g., financial transactions, billing).
  - Data structure is highly relational and benefits from complex joins and foreign keys.
  - Queries are unpredictable or require ad-hoc analytical filtering.
- **Choose Non-Relational (NoSQL) When**:
  - You need massive horizontal scalability (millions of writes/second) with low latency.
  - Data schema is flexible or constantly changing (e.g., user profiles, catalog attributes).
  - Queries are predictable and can be modeled around primary key lookups without joins.

---

## Q2: Explain the CAP Theorem and how AWS database services align with it.

The CAP Theorem states that a distributed system can guarantee at most two out of three characteristics: **Consistency**, **Availability**, and **Partition Tolerance**. In practice, partitions (network failures) are unavoidable, meaning distributed databases must choose between Consistency (C) and Availability (A) during network splits.

```text
                         CAP Theorem Trade-Off:
                         
                              Consistency (C)
                             (Strong Sync)
                             /           \
                            /   Network   \
                           /   Partition   \
                          /                 \
            Availability (A) ───────────── Partition Tolerance (P)
            (Eventual/Stale)               (Distributed Nodes)
```

- **CP (Consistency / Partition Tolerance)**:
  - System blocks write/read operations during network split to ensure no stale data is served.
  - **AWS Alignment**: **Amazon RDS (Multi-AZ)** storage replication is synchronous. If the primary cannot sync write operations to the standby, the write fails, prioritizing consistency. **Amazon MemoryDB** also acts as a CP system, requiring write confirmation to the transaction log.
- **AP (Availability / Partition Tolerance)**:
  - System processes writes and serves reads immediately, allowing eventual consistency across nodes.
  - **AWS Alignment**: **Amazon DynamoDB (Global Tables)** allows local writes/reads to succeed instantly in each region, replicating data asynchronously across regions, prioritizing availability. **RDS Read Replicas** also fit the AP model.

---

# AWS Relational Services (RDS & Aurora)

## Q3: What is the difference between Multi-AZ and Read Replicas in Amazon RDS?

This is one of the most critical RDS questions, focusing on the distinction between High Availability (HA) and scaling.

- **Multi-AZ Deployment**:
  - **Purpose**: High availability and disaster recovery.
  - **Replication**: Synchronous replication at the storage level. Data is written to the standby before acknowledging the client.
  - **Failover**: Automatic failover handled by RDS. DNS CNAME updates to point to the promoted standby.
  - **Access**: The standby is passive and cannot accept connections or read queries.
- **Read Replicas**:
  - **Purpose**: Horizontal read scaling and reporting offload.
  - **Replication**: Asynchronous replication at the database engine level (binlog/WAL).
  - **Failover**: No automatic failover. Must be manually promoted to a standalone instance.
  - **Access**: Replicas are active and readable by applications.

---

## Q4: Why would you choose Amazon Aurora over Amazon RDS?

Amazon Aurora is a cloud-optimized relational database. You choose it for higher scale, faster performance, and resilient failovers.

- **Storage Architecture**: Aurora uses a distributed, shared-storage volume that automatically replicates data 6 times across 3 Availability Zones. Standard RDS writes to a single EBS volume (and replicates to a standby EBS volume in Multi-AZ).
- **Failover Speed**: Aurora failovers typically take under 30 seconds because standby reader instances are already active and share the same storage volume. RDS failovers take 60-120 seconds.
- **Replication Lag**: Aurora replication lag is typically in single-digit milliseconds because reader instances read directly from the shared storage layer. RDS replicas rely on log replication, which can fall behind.
- **Scaling Limits**: Aurora supports up to 15 reader replicas and up to 128 TiB of auto-scaling storage. RDS supports up to 15 replicas (or 5 depending on configuration) and up to 64 TiB storage.

---

## Q5: How do you encrypt an existing unencrypted Amazon RDS instance with zero data loss?

You cannot enable encryption on an active unencrypted RDS instance directly. You must execute a snapshot-copy-restore migration:

1. Take a manual snapshot of the active unencrypted database.
2. Copy the snapshot to a new snapshot target, checking the option to enable encryption and specifying a KMS key.
3. Restore the encrypted snapshot to a new RDS instance.
4. Route client connection traffic to the new database endpoint.
5. Delete the old unencrypted instance.

---
