# EBS (Elastic Block Store)

## Definition

EBS is persistent, network-attached block storage for EC2 instances — the AWS equivalent of a virtual hard drive that exists independently of the instance's own lifecycle.

## Core Characteristics

- **Network-attached** — EBS traffic travels over the network (or, for Nitro instances, a dedicated EBS-optimized path), not a physical bus, which means there's inherent latency compared to local storage, though modern Nitro instances make this difference small for most workloads
- **Persistent** — survives instance stop and reboot; only deleted on termination if `DeleteOnTermination` is set for that volume (true by default for the root volume, false by default for additional volumes)
- **AZ-scoped** — a volume lives in exactly one Availability Zone and can only attach to instances in that same AZ
- **Single-attach by default** — a standard EBS volume attaches to exactly one instance at a time (see EBS Multi-Attach for the exception)
- **Detachable and re-attachable** — a volume can be detached from one instance and attached to another (within the same AZ), independent of either instance's own lifecycle

## Moving a Volume Across Availability Zones

EBS volumes cannot move between AZs directly. The standard path:

```text
1. Create a snapshot of the volume (snapshots are region-scoped, not AZ-scoped)
2. Restore the snapshot as a new volume in the target AZ
3. Attach the new volume to an instance in that AZ
```

## Use Cases

- The primary OS boot (root) volume for nearly every EC2 instance
- Relational databases requiring durable, consistent block storage
- General application storage that needs to persist independently of the instance

## Senior-Level Considerations

- "Stopped instances don't cost anything" is a common misconception — compute charges stop, but attached EBS volumes continue billing for their provisioned size and IOPS regardless of whether the instance is running
- Root volume `DeleteOnTermination` defaults to `true`, which is usually desired — but additional (non-root) volumes default to `false`, meaning they'll survive instance termination as orphaned, still-billing volumes unless explicitly deleted. This is a common source of accumulating, forgotten storage costs in real accounts
- See `EBS Volume Types.md` for choosing between gp3, io2, and the throughput-optimized (st1/sc1) families — the volume type is often a more consequential performance decision than the instance type itself for storage-bound workloads
