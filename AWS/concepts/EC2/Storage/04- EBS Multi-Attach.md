# EBS Multi-Attach

## Definition

Allows a single, specially-provisioned io1/io2 volume to be attached to multiple EC2 instances simultaneously, within the same Availability Zone — up to 16 instances.

## What It Does — and Critically, What It Doesn't

Multi-Attach solves the *attachment* problem: the same underlying block storage is reachable by multiple instances at once. It does **not** solve the *concurrent write coordination* problem — EBS itself has no built-in mechanism to prevent two instances from writing to the same block simultaneously and corrupting data. That responsibility falls entirely on the application or cluster software running on top of it.

```text
Instance A ──┐
             ├──► Multi-Attach EBS Volume (single io2, same AZ)
Instance B ──┘

EBS guarantees: both instances can read/write the same blocks
EBS does NOT guarantee: writes are coordinated or conflict-free
```

## Why It Requires a Cluster-Aware Filesystem or Application

A standard filesystem (ext4, XFS) assumes it's the only writer and will corrupt data if two instances mount and write to it independently without coordination. Multi-Attach is designed to be used with software that already handles distributed write coordination itself — a cluster-aware filesystem (like GFS2) or clustered database software (like Oracle RAC) that implements its own distributed locking on top of the shared block device.

## Constraints

- Only supported on io1/io2 volumes (Provisioned IOPS SSD) — not gp2/gp3, st1, or sc1
- All attached instances must be in the same Availability Zone as the volume
- Up to 16 concurrent attachments

## Common Real-World Use Case

Oracle RAC (Real Application Clusters) and similar clustered database architectures, where multiple database instances need shared access to the same underlying storage and already implement their own distributed coordination — this is essentially the primary reason Multi-Attach exists as a feature at all.

## Senior-Level Considerations

- Reaching for Multi-Attach for a workload that *doesn't* already have its own write-coordination logic is a near-guaranteed path to data corruption — this isn't a general-purpose "shared drive" feature, it's a narrow, specific building block for already-clustered software
- For the much more common "I need shared storage across multiple instances" need — a shared media folder, shared application state — EFS is almost always the right answer instead, since it's a real distributed filesystem designed for concurrent multi-client access from the ground up, rather than a shared block device requiring the application to handle coordination itself
