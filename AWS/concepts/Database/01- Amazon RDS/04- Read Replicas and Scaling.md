# RDS Read Replicas and Scaling

Relational databases often face read-heavy workloads where read queries (SELECTs) exhaust database CPU and memory, impacting write transactions. In Amazon RDS, **Read Replicas** solve this by enabling horizontal read scaling, separating transactional workloads from reporting, and providing cross-region disaster recovery options.

Understanding replication mechanics, replication lag, and promotion behavior is critical for scaling database-driven systems.

---

# Read Replicas Architecture

A Read Replica is a read-only copy of your primary database instance.

```text
       Client Application
       ├── Writes ──────────────────────────┐
       └── Reads (Load Balanced) ────┐      │
                                     ▼      ▼
┌──────────────────┐               ┌──────────────────┐
│  Read Replica    │               │   Primary DB     │
│  (Read-Only)     │               │   (Writable)     │
└────────▲─────────┘               └────────┬─────────┘
         │                                  │
         └───── Asynchronous Replication ───┘
                (Engine Binlog/WAL stream)
```

## Key Characteristics

- **Asynchronous Replication**: Replication occurs at the database engine level (e.g., binlog for MySQL, WAL for PostgreSQL). The primary writes data and immediately acknowledges the application. The write changes are streamed asynchronously to the read replica.
- **Active and Readable**: Read replicas are fully accessible. Applications can route reporting queries, search indexing, and dashboard queries to the replicas, keeping the primary free for write-heavy transactions.
- **Multiple Replicas**: You can create up to **15 read replicas** per primary database (or up to 5 for some database engines and setups).
- **Independent Sizing**: Replicas do not have to match the instance class or storage configuration of the primary, allowing you to size down replicas for low-traffic tasks or size up for heavy analytical queries.
- **Replica of Replica**: You can configure a read replica to replicate from another read replica (daisy-chaining) to reduce load on the primary, though this increases replication lag.

---

# Replication Lag

Because replication is asynchronous, there is a delay between when data is committed to the primary and when it appears on the replica. This is known as **Replication Lag** and is monitored in CloudWatch via the `ReplicaLag` metric (measured in seconds).

```text
Replication Lag Causes:

1. Long-Running Queries on Primary
   - A single transaction executing for 10 minutes must be applied 
     sequentially on the replica, stalling replication of subsequent writes.

2. Write-Heavy Workloads
   - A high rate of write operations on the primary can saturate the 
     replica's single-threaded replication worker or network link.

3. Different Hardware Capacity
   - If the replica is configured with a smaller instance class 
     (e.g., db.t3 vs db.r5), it may lack the CPU/memory to process WAL streams.

4. Network Latency (Cross-Region)
   - Transmitting log files across regions adds physical transit delay.
```

## Designing for Eventual Consistency

Applications using read replicas must be designed to tolerate **eventual consistency**:

- **Read-After-Write Consistency**: If a user updates their profile (write to primary) and immediately refreshes the page (read from replica), they may not see their update if replication lag is greater than a few milliseconds.
- **Mitigation**: Route critical, consistency-sensitive reads (e.g., authentication, checkout flows) directly to the primary, and use replicas for non-critical reads (e.g., feeds, historical data).

---

# Promoting a Read Replica

You can promote a read replica to a standalone, writable database instance.

```text
Read Replica (Read-Only)
       │
   Trigger "Promote"
       │
       ▼
1. RDS stops replication from the Primary database
       │
       ▼
2. RDS makes the instance writable (reboots instance)
       │
       ▼
3. The instance becomes a standalone primary database
```

## Common Use Cases for Promotion

- **Disaster Recovery**: If the primary region fails, promote a cross-region read replica to restore write capabilities in the secondary region.
- **Migration**: Migrate databases across accounts or regions by setting up a replica, waiting for sync, and promoting it during cutover.
- **Dev/Test Seed**: Create a read replica of production, promote it to a standalone instance, and use it for safe testing against realistic datasets.

---

# Cross-Region Read Replicas

RDS supports deploying read replicas in different AWS regions than the primary.

- **DR Strategy**: Cross-region replicas provide low Recovery Point Objective (RPO) disaster recovery targets.
- **Geo-Proximity Reads**: Reduce read latency for global users by routing local reads to cross-region replicas.
- **Data Transfer Costs**: Data replication across regions incurs standard AWS cross-region data transfer fees, which can be significant for high-write workloads.
- **Security**: Replication traffic across regions is automatically encrypted by AWS over the internal transit network.

---

# Write Scaling Options

Read replicas only scale **reads**. Relational databases are notoriously difficult to scale for writes. If writes exhaust your primary database capacity, consider:

- **Database Sharding**: Split data horizontally across multiple independent RDS instances at the application layer.
- **Aurora**: Migrate to Amazon Aurora, which scales write workloads more efficiently via distributed storage and optimized lock management.
- **Write Delegation / Queueing**: Place an SQS queue in front of database writes to smooth out spikes in traffic.

---

# Key Takeaways

- **Read Replicas** use asynchronous replication to offload read-only queries from the primary.
- Applications must handle **eventual consistency** due to **Replication Lag**.
- CloudWatch metric `ReplicaLag` monitors replication health; keep instance classes comparable to prevent lag.
- Replicas can be **promoted** to standalone databases for DR, migration, or testing.
- Cross-region replicas provide global read performance and disaster recovery capabilities.

---
