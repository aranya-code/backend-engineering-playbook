# Storage

Block, instance, and file storage options for EC2 — what each is actually for, and where they stop being interchangeable.

---

| # | Topic | Description |
|---|-------|-------------|
| 01 | [EBS](01-%20EBS.md) | Persistent, network-attached block storage — AZ-scoped, single-instance by default |
| 02 | [EBS Volume Types](02-%20EBS%20Volume%20Types.md) | gp3, io2, st1/sc1 — choosing by IOPS, throughput, and cost |
| 03 | [EBS Snapshot](03-%20EBS%20Snapshot.md) | Incremental backups, cross-region copy, and automating lifecycle with DLM |
| 04 | [EBS Multi-Attach](04-%20EBS%20Multi-Attach.md) | Shared block access for already-clustered software — attachment only, not write coordination |
| 05 | [Instance Store](05-%20Instance%20Store.md) | Physically local, ephemeral storage — fastest, but lost on stop/terminate |
| 06 | [EFS](06-%20EFS.md) | A real distributed filesystem for concurrent multi-instance, multi-AZ access |
| 07 | [IOPS](07-%20IOPS.md) | IOPS vs. throughput vs. latency, and diagnosing a storage bottleneck |

---

## 🔗 See Also

- [`../`](../) — EC2 overview
- [`../Troubleshooting/04- High CPU and T-Series Throttling.md`](../Troubleshooting/04-%20High%20CPU%20and%20T-Series%20Throttling.md) — a related but distinct performance investigation

---

*Part of the [backend-engineering-playbook](../../../../) knowledge base — Aranya Majumdar*
