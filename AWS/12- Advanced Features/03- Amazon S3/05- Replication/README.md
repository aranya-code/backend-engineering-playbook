# README

## Overview

This section covers S3 replication for maintaining copies of objects across buckets. It introduces replication fundamentals, Cross-Region Replication (CRR), Same-Region Replication (SRR), replication metrics, and Replication Time Control (RTC).

Use these documents when designing disaster recovery, regional data distribution, compliance copies, or operational separation between source and destination buckets. Replication is asynchronous and depends on correct bucket versioning, IAM permissions, destination configuration, encryption permissions, and rule scope.

## Navigation

| # | Document | Description |
|---|---|---|
| 01 | [S3 Replication Fundamentals](./01-%20S3%20Replication%20Fundamentals.md) | Replication prerequisites, rule structure, eligible objects, permissions, and operational behavior |
| 02 | [Cross-Region Replication (CRR)](./02-%20Cross-Region%20Replication%20(CRR).md) | Replicating objects to a bucket in another AWS Region for geographic separation and regional recovery |
| 03 | [Same-Region Replication (SRR)](./03-%20Same-Region%20Replication%20(SRR).md) | Replicating objects between buckets in the same Region for workload separation and data distribution |
| 04 | [Replication Metrics and Monitoring](./04-%20Replication%20Metrics%20and%20Monitoring.md) | Monitoring pending operations, replication latency, failures, and replication status |
| 05 | [Replication Time Control (RTC)](./05-%20Replication%20Time%20Control%20(RTC).md) | Using a defined replication time objective with metrics and operational monitoring |

## Suggested Reading Order

1. Start with replication prerequisites, permissions, and rule behavior.
2. Compare CRR and SRR against the required failure-domain and data-distribution objectives.
3. Configure metrics and alerts before relying on replication operationally.
4. Evaluate RTC when the workload requires a predictable replication time objective.

## Operational Considerations

- Enable versioning on both source and destination buckets.
- Verify the replication role, destination permissions, and KMS permissions for encrypted objects.
- Define how existing objects, delete markers, and replica ownership should be handled.
- Do not treat replication as a backup by itself; deletion and other changes can also be replicated depending on configuration.
- Monitor replication status and test recovery from the destination.

## Key Takeaways

- Replication is asynchronous and requires versioning and correctly scoped permissions.
- Choose CRR or SRR based on the required geographic separation and workload architecture.
- Monitor replication status and latency instead of assuming that a successful source write means the replica is ready.
- Validate encryption, ownership, delete-marker, and existing-object behavior as part of rollout.
