# RDS Monitoring and Observability

To run relational databases reliably in production, you must have visibility into resource utilization, active sessions, query execution statistics, and performance bottlenecks. Amazon RDS provides three layers of monitoring: **Standard CloudWatch Metrics**, **Enhanced Monitoring**, and **Performance Insights**.

Understanding which tool to use, how to interpret metrics, and how to troubleshoot common database failures is essential for database reliability engineering.

---

# 1. Standard CloudWatch Metrics

Standard metrics are gathered from the hypervisor level. They reflect host resource utilization and basic database stats.

## Critical Metrics to Monitor

- **CPUUtilization**: Percentage of CPU utilized. High CPU (constant >80%) indicates under-provisioned instance classes, missing database indexes, or unoptimized queries.
- **DatabaseConnections**: Number of active client connections. Spikes in connections can saturate database memory and file descriptors.
- **FreeableMemory**: Amount of available RAM. If this drops close to zero, the OS may trigger Out-Of-Memory (OOM) kills or begin swapping, severely degrading performance.
- **WriteIOPS / ReadIOPS**: The number of I/O operations per second. Compare these against your provisioned storage limits (gp3/io2 baseline vs max IOPS).
- **WriteLatency / ReadLatency**: The average time taken for I/O operations (in seconds). Spikes indicate disk saturation.
- **ReplicaLag**: Replication delay for read replicas. High lag indicates heavy transactions, locking, or saturated resources on the replica.

---

# 2. Enhanced Monitoring

While standard CloudWatch metrics run at the hypervisor level at 60-second intervals, Enhanced Monitoring gathers OS-level metrics directly from an agent running inside the database virtual machine.

- **Granularity**: Can be configured down to **1-second intervals** (standard is 60 seconds).
- **Scope**: Measures CPU usage details (System, User, Nice, I/O Wait), memory details (Active, Cached, Slab), process list with CPU/Memory usage per process, and disk device utilization.
- **Use Case**: Critical for diagnosing short, transient spikes in resource usage, understanding context switching, identifying which database process is consuming resources, and analyzing I/O wait times.

```text
Standard CloudWatch Metrics        Enhanced Monitoring
(Hypervisor Level)                 (OS VM Level via Agent)
┌───────────────────────┐          ┌───────────────────────┐
│  vCPU Utilization     │          │  User vs. System CPU  │
│  EBS Volume IOPS      │          │  Active Process List  │
│  Network Byte Count   │          │  I/O Wait Times       │
│  (60s intervals)      │          │  (1s - 60s intervals) │
└───────────────────────┘          └───────────────────────┘
```

---

# 3. Performance Insights

Performance Insights is a database performance tuning tool that visualizes **Database Load** (measured in Average Active Sessions - AAS) and categorizes it by wait states, SQL queries, hosts, and users.

## Understanding DB Load and AAS

Database Load represents the average number of active database connections executing work at any given point in time.

- **AAS = 1**: On average, exactly one session is active.
- **Max vCPU Line**: Represents the physical limits of the database host.
  - If **DB Load is below the Max vCPU line**, the database has excess capacity.
  - If **DB Load is above the Max vCPU line**, sessions are queuing up, indicating a bottleneck.

```text
DB Load (Average Active Sessions)
  5 │                  *     *
  4 │             *    *  *  *  *
----│-------------*----*--*--*--*--------  ◄── Max vCPU Line (4 vCPUs)
  2 │        *    *    *  *  *  *  *
  1 │   *    *    *    *  *  *  *  *  *
    └───┴────┴────┴────┴────┴────┴───┴──► Time
```

## Wait States Analysis

Performance Insights categorizes load by **Wait States** (why the query is waiting):

- **CPU**: The query is executing calculations (indicates missing indexes or poor query plans).
- **IO:XactSync / IO:DataFileRead**: The query is waiting for disk reads or database commits (indicates slow storage, insufficient RAM, or heavy writes).
- **Lock:transaction**: The query is waiting for another transaction to release a lock on a table or row.

---

# Troubleshooting Production Failures

## CPU Spikes

- **Indicators**: `CPUUtilization` at 100%, application latency spikes, `DatabaseConnections` increase.
- **Diagnostic**: Check **Performance Insights** to find the top SQL query causing the load. Look for high CPU wait states.
- **Solution**: Run `EXPLAIN` on the query to find missing indexes, optimize query structure, or scale up the instance class.

## High Database Connections

- **Indicators**: `DatabaseConnections` matches database limits, clients receive `Too many connections` errors.
- **Diagnostic**: Check if connection spike aligns with an application scale-out event (e.g., Lambda scaling).
- **Solution**: Deploy **RDS Proxy** to pool connections, or increase the `max_connections` parameter in parameter groups (requires memory validation).

## Disk Space Exhaustion

- **Indicators**: `FreeStorageSpace` drops to zero, database becomes read-only or crashes.
- **Diagnostic**: Check if storage auto-scaling reached its maximum limit. Look for large temp tables created by unindexed queries.
- **Solution**: Increase storage size (trigger manual scale-up) or resolve unindexed sorting queries generating large temporary files.

---

# Key Takeaways

- **Standard CloudWatch Metrics** provide hypervisor-level stats (60s intervals) for baseline resource monitoring.
- **Enhanced Monitoring** runs an OS agent (down to 1s granularity) to capture detailed I/O wait times and process lists.
- **Performance Insights** measures database load (Average Active Sessions - AAS) and pinpoints bottlenecks via wait states (CPU, I/O, Lock).
- Configure alerts on **CPUUtilization**, **FreeableMemory**, and **FreeStorageSpace** to catch issues before outages occur.

---
