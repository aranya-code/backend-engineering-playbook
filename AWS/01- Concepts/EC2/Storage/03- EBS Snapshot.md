# EBS Snapshots

## Definition

A point-in-time backup of an EBS volume, stored in S3 (though not directly visible or accessible as an S3 object) and usable to create new volumes, copy data across Availability Zones, or copy across Regions.

## Incremental by Design

The first snapshot of a volume captures the entire volume's data. Every snapshot after that is **incremental** — it only stores the blocks that changed since the previous snapshot, not a full copy each time. Deleting an intermediate snapshot in a chain doesn't break the ones after it; AWS's internal snapshot mechanism preserves whatever blocks are still needed by remaining snapshots.

## Detaching Before a Snapshot — Not Mandatory, But Consider Consistency

It's possible to take a snapshot of a volume while it's still attached and in active use, and AWS does ensure the snapshot itself is crash-consistent (equivalent to what you'd get from a sudden power loss). For applications sensitive to in-flight writes at the moment of the snapshot (databases in particular), briefly pausing writes, flushing to disk, or using an application-aware backup mechanism produces a more reliable restore point than relying on crash consistency alone.

## Copying Across Regions and Availability Zones

- **Across Availability Zones** (within the same Region) — restore the snapshot as a new volume directly in the target AZ; this is also the standard mechanism for "moving" a volume between AZs at all, since volumes themselves can't move directly
- **Across Regions** — snapshots can be explicitly copied to another Region, which is the foundation of many EBS-based disaster recovery and multi-region strategies

## Fast Snapshot Restore (FSR)

By default, a newly restored volume from a snapshot can have a brief performance dip on first access to any given block (a "lazy load" from the snapshot data), which matters for latency-sensitive workloads that need full performance immediately upon restore. Fast Snapshot Restore pre-warms specified snapshots in specified AZs, eliminating this initial latency penalty — at an additional ongoing cost per snapshot/AZ combination enabled.

## Automating Snapshot Lifecycle

Manually managing snapshot creation and cleanup doesn't scale. **Amazon Data Lifecycle Manager (DLM)** automates scheduled snapshot creation, retention (how many to keep, or for how long), and cleanup of old snapshots based on defined policies — the standard production approach rather than relying on manual or ad hoc scripted snapshots.

## Senior-Level Considerations

- Incremental snapshot billing means the *storage cost* of a snapshot reflects only the changed blocks it uniquely holds — but restoring any single snapshot in a chain reconstructs the full volume state at that point in time regardless, since AWS manages the underlying block relationships transparently
- Snapshots are the standard building block for AMI creation as well (creating an AMI from an instance snapshots all its attached EBS volumes) — understanding snapshots directly clarifies why custom AMI creation takes the time it does, proportional to data changed since the last snapshot
- A snapshot-based DR strategy's actual RPO is bounded by snapshot frequency — snapshotting only once a day means up to 24 hours of data loss in a worst-case failure, which should be an explicit, deliberate part of any DR planning (see the Disaster Recovery Strategies file in AWS-Architecture) rather than an assumed detail
