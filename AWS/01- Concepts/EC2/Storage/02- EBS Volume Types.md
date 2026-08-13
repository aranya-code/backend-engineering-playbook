# EBS Volume Types

EBS offers several volume types, each optimized for a different performance profile and cost point. Choosing the right one is a genuinely consequential production decision, not a minor detail.

## SSD-Backed Volumes (Low Latency, High IOPS)

| Type | Baseline IOPS | Max IOPS | Best For |
|---|---|---|---|
| **gp3** (General Purpose SSD, current gen) | 3,000, independent of size | 16,000 (provisionable) | Default choice for almost everything — boot volumes, most databases, general applications |
| **gp2** (General Purpose SSD, previous gen) | 3 IOPS per GB (min 100) | 16,000 | Legacy — largely superseded by gp3, which decouples IOPS from volume size |
| **io2 / io2 Block Express** (Provisioned IOPS SSD) | Provisioned explicitly | Up to 256,000 (Block Express) | Mission-critical, latency-sensitive databases (large-scale OLTP, SAP HANA) needing sustained, guaranteed high IOPS |
| **io1** (Provisioned IOPS SSD, previous gen) | Provisioned explicitly | Up to 64,000 | Legacy — largely superseded by io2, which offers better durability at the same price |

## HDD-Backed Volumes (High Throughput, Not Low Latency)

| Type | Optimized For | Best For |
|---|---|---|
| **st1** (Throughput Optimized HDD) | Sequential throughput (MB/s), not IOPS | Big data, log processing, data warehouses — large sequential reads/writes |
| **sc1** (Cold HDD) | Lowest cost per GB | Infrequently accessed data, archival workloads where cost matters more than performance |

**Critical distinction:** st1/sc1 **cannot** be used as a boot volume, and are measured in throughput (MB/s), not IOPS — using one for a random-access, high-IOPS workload (like a database) will perform very poorly regardless of volume size.

## Why gp3 Is the Default Recommendation Today

Unlike gp2 (where IOPS scaled with — and were capped by — volume size, forcing you to over-provision storage just to get more IOPS), gp3 decouples IOPS and throughput from size entirely: a small gp3 volume can have the same 3,000 baseline IOPS as a much larger one, and both IOPS and throughput can be provisioned independently for a predictable additional cost. This is both cheaper and more flexible than gp2 for the overwhelming majority of workloads, which is why AWS positions it as the default choice.

## Choosing Between io2 and gp3

The decision point is usually: does the workload need **guaranteed, sustained** high IOPS (io2, provisioned and guaranteed) or is gp3's baseline (with burst-like headroom up to its provisioned max) sufficient? Large-scale, latency-sensitive production databases with unpredictable spiky access patterns are the classic io2 use case; most general application and moderate-database workloads are well served by gp3.

## Senior-Level Considerations

- IOPS and throughput are two different things worth being precise about: IOPS measures the number of read/write operations per second (relevant for many small, random operations — typical of databases), while throughput measures MB/s (relevant for large sequential transfers — typical of media processing or log ingestion). A workload can be IOPS-bound while having plenty of throughput headroom, or vice versa
- Volume type can be changed on a live, in-use volume (an "elastic volume" modification) without downtime — there's rarely a good reason to leave a workload on legacy gp2/io1 today given gp3/io2 offer better performance-per-dollar with no migration downtime required
- Because st1/sc1 can't be a boot volume and perform poorly for random access, mixing volume types on a single instance (a fast gp3/io2 root + database volume, plus an st1 volume for log archival) is a common, deliberate production pattern rather than an inconsistency
