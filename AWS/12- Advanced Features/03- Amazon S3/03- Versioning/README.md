# README

## Overview

This section covers S3 bucket versioning and its impact on object updates, deletes, recovery, lifecycle management, and replication. It explains how S3 retains multiple versions of an object, how delete markers affect ordinary reads, and how versioning interacts with MFA Delete and other bucket features.

Use these documents when implementing recovery controls, protecting data from accidental overwrites or deletions, and designing retention policies. Versioning improves recoverability, but it does not replace backups, access controls, lifecycle policies, or tested recovery procedures.

## Navigation

| # | Document | Description |
|---|---|---|
| 01 | [S3 Versioning Fundamentals](./01-%20S3%20Versioning%20Fundamentals.md) | Versioning states, version IDs, object update behavior, and bucket-level configuration |
| 02 | [Delete Markers and Object Versions](./02-%20Delete%20Markers%20and%20Object%20Versions.md) | Delete-marker behavior, version-specific reads, and recovery of previous object versions |
| 03 | [MFA Delete](./03-%20MFA%20Delete.md) | Additional authentication requirements for permanent version deletion and versioning suspension |
| 04 | [Versioning and Lifecycle Integration](./04-%20Versioning%20and%20Lifecycle%20Integration.md) | Lifecycle behavior for current and noncurrent versions, expiration, and cleanup |
| 05 | [Versioning and Replication Integration](./05-%20Versioning%20and%20Replication%20Integration.md) | Versioning prerequisites and how object versions interact with replication configuration |

## Suggested Reading Order

1. Understand versioning states and version IDs.
2. Learn how delete markers differ from permanent version deletion.
3. Review MFA Delete as an additional protection control.
4. Study lifecycle and replication integration before applying bucket-wide policies.

## Key Takeaways

- Enable versioning deliberately and understand that versioning can be enabled or suspended but not returned to the never-versioned state.
- A simple delete in a versioning-enabled bucket generally creates a delete marker; it does not permanently remove prior versions.
- Noncurrent versions continue to incur storage charges until explicitly expired or deleted.
- Validate lifecycle and replication behavior against versioning requirements before applying production changes.
