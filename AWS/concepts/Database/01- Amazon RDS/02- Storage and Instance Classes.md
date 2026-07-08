# RDS Storage and Instance Classes

Database performance depends heavily on the underlying hardware allocation. In Amazon RDS, this is determined by two main factors: the **Storage Type** (which dictates disk I/O performance and capacity) and the **DB Instance Class** (which dictates CPU, memory, and network throughput limits).

Understanding these choices, how storage auto-scaling works, and how to select the right instance class is critical for optimizing database performance and cost.

---

# RDS Storage Types

RDS uses Amazon EBS network-attached storage. There are four primary storage types available:

## 1. General Purpose SSD (gp3) - Recommended

gp3 is the latest generation of general-purpose SSD storage. It decouples storage size, IOPS, and throughput.

- **Baseline Performance**: 3,000 IOPS and 125 MB/s throughput included for all storage sizes.
- **Scalability**: Independently scale IOPS up to 16,000 (for gp3 on RDS) and throughput up to 1,000 MB/s.
- **Cost**: More cost-effective than gp2 and Provisioned IOPS (io1/io2) for standard workloads.
- **Best Use Case**: Most production databases, development environments, and applications with moderate, predictable I/O demands.

## 2. General Purpose SSD (gp2)

gp2 links performance directly to the storage volume size.

- **Baseline Performance**: 3 IOPS per GB, with a minimum baseline of 100 IOPS.
- **Burst Performance**: Volumes under 1,000 GB can burst up to 3,000 IOPS using I/O credits accumulated during idle times.
- **Limitation**: To get 3,000 baseline IOPS, you must provision at least 1,000 GB of storage, leading to over-provisioning storage just for performance.
- **Best Use Case**: Legacy workloads (migrate to gp3 for better cost-to-performance).

## 3. Provisioned IOPS SSD (io1 & io2 Block Express)

Designed for heavy, I/O-intensive workloads.

- **Performance**: Predictable, low-latency performance where you explicitly provision the required IOPS independently of storage size.
- **io2 Block Express**: Offers up to 256,000 IOPS, 4,000 MB/s throughput, and sub-millisecond latency. io2 provides 100x higher durability than io1.
- **Best Use Case**: High-throughput OLTP databases, large enterprise applications, and workloads requiring consistent, maximum I/O performance.

---

# Storage Comparison Table

| Metric / Feature | gp2 | gp3 | io1 | io2 Block Express |
|------------------|-----|-----|-----|-------------------|
| **Max Capacity** | 64 TiB | 64 TiB | 64 TiB | 64 TiB |
| **Max IOPS** | 16,000 | 16,000 | 64,000 | 256,000 |
| **Max Throughput**| 250 MB/s | 1,000 MB/s | 1,000 MB/s | 4,000 MB/s |
| **Performance Model**| Tied to size (3 IOPS/GB) | Decoupled | Decoupled | Decoupled |
| **Durability** | 99.8% - 99.9% | 99.8% - 99.9% | 99.8% - 99.9% | 99.999% |
| **Cost** | Baseline | Low-to-Moderate| High | Premium |

---

# RDS Storage Auto Scaling

RDS Storage Auto Scaling allows the database to automatically increase its storage capacity when free space falls below a threshold, preventing database outages caused by out-of-space conditions (`Storage Full` errors).

```text
Free Storage Space < 10% of Allocated Storage
       AND
Low Disk Space condition persists for > 5 minutes
       AND
At least 6 hours have passed since the last storage modification
       │
       ▼
RDS triggers Auto Scaling
   Increases storage by:
   - 10% of current allocated storage, OR
   - 10 GB (whichever is greater)
```

## Critical Operational Rules

- **Scale Up Only**: Storage auto-scaling **only scales upward**. You cannot decrease the storage size of an RDS instance once it has been increased. To reduce storage, you must export data, create a smaller database instance, and import the data.
- **Maximum Storage Limit**: You must define a **Maximum Storage Threshold** to prevent runaway scaling from consuming unnecessary costs (e.g., due to log file leaks or rogue queries).
- **Modification Cool-down**: After storage is scaled up (manually or automatically), further storage modifications are blocked for a cool-down period of **6 hours**.

---

# DB Instance Classes

DB instance classes determine the compute (vCPUs) and memory (RAM) allocated to the RDS instance.

## 1. Standard Classes (db.m6g, db.m5)

General-purpose instances balanced for compute, memory, and network performance.
- **Best Use Case**: Standard production workloads.

## 2. Memory-Optimized Classes (db.r6g, db.r5, db.x8g)

Provide a higher ratio of RAM to vCPU.
- **Why RAM matters**: Relational databases perform best when their active dataset (working set) fits entirely in memory, avoiding slow disk reads.
- **Best Use Case**: High-performance production databases, intensive query workloads, and large OLTP systems.

## 3. Burstable Classes (db.t4g, db.t3)

Provide baseline CPU performance with the ability to burst above the baseline using CPU credits.
- **Warning**: If you exhaust CPU credits, CPU performance is throttled to the baseline, which can cause query latency to skyrocket and application connections to pile up.
- **Best Use Case**: Development, staging, low-traffic databases, and non-production testing. Never use burstable instances for production databases with unpredictable traffic.

---

# EBS-Optimized DB Instances

Almost all modern RDS DB instances are **EBS-optimized**. This means they have dedicated network bandwidth specifically for I/O traffic between the instance and the EBS volume, separated from regular network traffic (e.g., client SQL connections).

If database query times are high, check the instance's **EBS Bandwidth limits** and **EBS IOPS limits** in CloudWatch to ensure the instance itself is not bottlenecking I/O, even if the storage disk has remaining IOPS.

---

# Key Takeaways

- **gp3** is the default recommended storage type, offering independent scaling of IOPS and throughput at a lower cost than gp2.
- **Storage Auto Scaling** only scales up; it never scales down. Set a maximum limit to prevent unexpected billing.
- Database scaling requires a **6-hour cool-down** period between changes.
- **Memory-optimized (db.r* / db.x*)** instances are preferred for production relational databases to keep the working set cached in memory.
- Avoid using burstable (**db.t***) instances in production to prevent performance throttling when CPU credits are exhausted.

---
