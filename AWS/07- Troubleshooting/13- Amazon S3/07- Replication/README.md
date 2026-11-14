# README

## Overview

Amazon S3 replication troubleshooting covers the diagnostic workflows and corrective procedures for failures in Cross-Region Replication (CRR) and Same-Region Replication (SRR) configurations. It addresses objects that are not replicated, replication that stalls or falls behind, permission failures in the replication IAM role, and the status inspection workflows used to verify that replication is operating correctly.

This section provides structured guidance for diagnosing replication failures at each layer: bucket configuration, IAM replication role permissions, destination bucket policy, encryption key access, and object eligibility conditions.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Cross-Region Replication Issues](./01-%20Cross-Region%20Replication%20Issues.md) | Diagnosing CRR configuration failures, objects not replicated, replication lag, and cross-region permission gaps |
| 02 | [02- Same-Region Replication Issues](./02-%20Same-Region%20Replication%20Issues.md) | Diagnosing SRR failures within the same region, cross-account SRR permission requirements, and object eligibility |
| 03 | [03- Replication Permissions and Status](./03-%20Replication%20Permissions%20and%20Status.md) | Verifying IAM replication role permissions, destination bucket policies, KMS key access, and replication status inspection |

## Why Replication Troubleshooting Matters

Replication failures are often silent — objects that fail to replicate do not produce application errors at the source. The failure only becomes apparent when the destination bucket is inspected, replication metrics show a growing pending object count, or a disaster recovery test reveals that the destination does not contain the expected data.

Common causes include:

- Replication IAM role missing `s3:ReplicateObject` or `s3:ReplicateDelete` on the destination bucket resource ARN.
- Destination bucket policy not granting the replication role permission to write objects, which is required for cross-account replication.
- Objects uploaded before replication was enabled are not replicated — replication only applies to objects uploaded after the rule is created.
- SSE-KMS encrypted objects not replicated because the replication role lacks `kms:Decrypt` on the source key and `kms:GenerateDataKey` on the destination key.
- Object not matched by the replication rule filter due to prefix mismatch, tag condition, or storage class exclusion.
- Destination bucket does not have versioning enabled, which is a requirement for all S3 replication configurations.

## Core Troubleshooting Principle

Start replication diagnostics by checking replication metrics in CloudWatch for `ReplicationLatency` and `BytesPendingReplication`. Then inspect individual object replication status using `aws s3api head-object` and review the `ReplicationStatus` field. Check the replication role's effective permissions against the destination bucket and, for SSE-KMS objects, against both the source and destination KMS keys.

## Key Takeaways

- Replication only applies to objects uploaded after the replication rule is created; existing objects are not retroactively replicated without a S3 Batch Operations job.
- Cross-account replication requires both a correctly configured IAM replication role and a destination bucket policy that explicitly grants the role write access.
- SSE-KMS encrypted object replication requires the replication IAM role to have `kms:Decrypt` on the source key and `kms:GenerateDataKey` on the destination key.
