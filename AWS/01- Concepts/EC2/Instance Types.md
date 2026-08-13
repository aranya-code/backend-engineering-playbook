# EC2 Instance Types

# Instance Naming Convention

Every EC2 instance type follows a structured naming pattern:

```text
  m   5   a   .  xlarge
  │   │   │      │
  │   │   │      └── Size (nano, micro, small, medium, large, xlarge, 2xlarge, ..., metal)
  │   │   │
  │   │   └── Additional Attributes (optional)
  │   │       a = AMD processor
  │   │       g = Graviton (ARM) processor
  │   │       d = Local NVMe instance store
  │   │       n = Enhanced networking
  │   │       e = Extra memory or storage
  │   │
  │   └── Generation (higher = newer, better price-performance)
  │
  └── Family (defines the primary optimization)

Examples:
  m7g.large    = General Purpose, Gen 7, Graviton, Large
  c6i.xlarge   = Compute Optimized, Gen 6, Intel, Extra Large
  r5dn.2xlarge = Memory Optimized, Gen 5, local NVMe + enhanced networking, 2XL
```

---

# Instance Families

## General Purpose (M, T)

Balanced compute, memory, and networking. The default choice when no specific optimization is needed.

### M-Series (Fixed Performance)
- Consistent baseline performance at all times
- Use case: application servers, mid-size databases, backend APIs, microservices
- Examples: m7g.large, m6i.xlarge, m5.2xlarge

### T-Series (Burstable Performance)
- Baseline CPU allocation with burst capability via **CPU credits**
- Significantly cheaper than M-series for variable workloads
- Examples: t3.micro, t3.medium, t3a.large (AMD variant)

**T3 CPU Credit Model:**

```text
CPU Utilization
100% ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
      │            Burst                    │
      │         ┌────────┐                  │
      │         │ Credits│                  │
      │         │ Spent  │                  │
 20% ─├─────────┘        └──────────────────┤── Baseline
      │  Credits Accumulating               │
  0% ─┴────────────────────────────────────┴──
      Time ──────────────────────────────────►

Standard Mode: When credits run out, CPU is capped at baseline.
Unlimited Mode: Can burst beyond credits (charged per vCPU-hour over baseline).
```

**Production Warning**: A t3.medium has a 20% CPU baseline. Under sustained load, standard mode throttles to 20% — your application becomes 5x slower. Monitor `CPUCreditBalance` in CloudWatch. If credits reach zero, upgrade to M-series.

---

## Compute Optimized (C)

Highest compute performance per dollar. More vCPUs relative to memory.

- Use case: batch processing, ML inference, video encoding, gaming servers, scientific modeling, high-performance web servers
- Examples: c7g.xlarge (Graviton), c6i.2xlarge (Intel), c5.4xlarge

---

## Memory Optimized (R, X, z)

High memory-to-vCPU ratio. Designed for workloads that process large datasets in memory.

| Sub-Family | RAM Range | Use Case |
|-----------|-----------|----------|
| R-series | Up to 768 GiB | In-memory caches (Redis, Memcached), real-time analytics |
| X-series | Up to 3,904 GiB | SAP HANA, in-memory databases |
| z1d | Up to 384 GiB | High single-thread performance + high memory |

---

## Storage Optimized (I, D, H)

High sequential read/write access to large datasets on local storage.

| Sub-Family | Storage Type | Use Case |
|-----------|-------------|----------|
| I-series (i3, i3en, i4i) | NVMe SSD (millions of IOPS) | NoSQL databases (Cassandra, DynamoDB local), real-time analytics |
| D-series (d2, d3) | Dense HDD (up to 48 TB) | Data warehousing, HDFS, distributed file systems |
| H-series (h1) | HDD (up to 16 TB) | MapReduce, log processing |

---

## Accelerated Computing (P, G, Inf, Trn, DL)

Specialized hardware accelerators (GPUs, custom chips) attached to the instance.

| Sub-Family | Accelerator | Use Case |
|-----------|------------|----------|
| P-series (p4d, p5) | NVIDIA A100/H100 GPUs | ML training, HPC, deep learning |
| G-series (g5, g6) | NVIDIA T4/L4 GPUs | Graphics rendering, video transcoding, ML inference |
| Inf-series (inf2) | AWS Inferentia chips | Cost-effective ML inference at scale |
| Trn-series (trn1) | AWS Trainium chips | ML training (purpose-built, cheaper than GPUs) |

---

# Graviton Instances (ARM)

AWS Graviton processors are custom ARM-based chips designed by AWS.

| Feature | Intel/AMD (x86) | Graviton (ARM) |
|---------|----------------|----------------|
| Price | Baseline | ~20% cheaper |
| Performance | Standard | Up to 40% better price-performance |
| Compatibility | Universal | Most Linux workloads, containers, Java, Python, Node.js |
| Instance suffix | `i` (Intel), `a` (AMD) | `g` (Graviton) |

**When to use Graviton**: Any workload that doesn't depend on x86-specific libraries. Containerized workloads, web servers, microservices, and databases all run well on Graviton.

**When NOT to use**: Workloads requiring x86 binaries, Windows (limited), or specific hardware instruction sets.

---

# Instance Selection Decision Tree

```text
What is your primary workload?
│
├── General web app / API? ──────────────────► M7g or T3 (if variable load)
│
├── Heavy computation (batch, encoding)? ────► C7g (Graviton) or C6i (Intel)
│
├── Large in-memory dataset? ────────────────► R7g (up to 768 GiB RAM)
│                                              X2idn (up to 3,904 GiB)
│
├── High-IOPS local storage? ────────────────► I4i (NVMe SSD)
│
├── ML Training? ────────────────────────────► P5 (NVIDIA H100) or Trn1
│
├── ML Inference? ───────────────────────────► Inf2 (cheapest) or G5
│
└── Dev/test with variable load? ────────────► T3a.medium (AMD, cheapest burst)
```

---

# Instance Size Progression

All instance families follow the same size scaling pattern:

```text
Size        vCPUs    Memory (varies by family)
─────────   ─────    ─────────────────────────
nano          1        0.5 GiB (T-series only)
micro         1        1 GiB
small         1        2 GiB
medium        1        4 GiB
large         2        8 GiB
xlarge        4       16 GiB
2xlarge       8       32 GiB
4xlarge      16       64 GiB
8xlarge      32      128 GiB
12xlarge     48      192 GiB
16xlarge     64      256 GiB
24xlarge     96      384 GiB
metal        96+     384+ GiB (bare metal, no hypervisor)

Note: Exact memory values vary by family (R-series has more per vCPU).
Each step doubles vCPUs and memory from the previous size.
```

---

# Common Mistakes

- Using T-series in standard mode for sustained workloads — CPU gets throttled when credits exhaust.
- Not considering Graviton instances — 20% cheaper with equivalent or better performance for most workloads.
- Choosing instance type before understanding the workload profile. A CPU-bound app on R-series wastes expensive memory.
- Not monitoring T3 `CPUCreditBalance` — silent performance degradation when credits hit zero.
- Over-sizing instances from day one instead of right-sizing with CloudWatch metrics and Compute Optimizer.

---

# Key Takeaways

- Instance type naming follows `[family][generation][attributes].[size]` — learn to read it.
- T-series burstable instances use CPU credits. Monitor them or use Unlimited mode.
- Graviton (ARM) instances provide ~20% cost savings with equivalent performance for most Linux workloads.
- Match the family to the bottleneck: C for CPU, R for memory, I for storage IOPS, P/Inf/Trn for ML.
- Use AWS Compute Optimizer to right-size instances based on actual utilization data.
- Start with general purpose (M/T), then optimize after you have production utilization metrics.

---
