# Disaster Recovery Strategies

AWS commonly frames DR strategy as four tiers, trading cost against recovery speed (RTO — Recovery Time Objective) and data loss tolerance (RPO — Recovery Point Objective).

## The Four Strategies

| Strategy | RTO | RPO | Relative Cost |
|---|---|---|---|
| Backup & Restore | Hours | Hours (since last backup) | Lowest |
| Pilot Light | ~10s of minutes | Minutes | Low-Medium |
| Warm Standby | Minutes | Seconds-Minutes | Medium-High |
| Multi-Site Active-Active | Near-zero | Near-zero | Highest |

## Backup & Restore

Regularly back up data (e.g., RDS snapshots, S3 cross-region replication) to a second Region; infrastructure itself isn't running there until needed, and is provisioned from scratch (or from infrastructure-as-code) during an actual disaster.

**Trade-off:** cheapest by far, but recovery genuinely takes hours — acceptable for workloads where an extended outage is costly but survivable.

## Pilot Light

A minimal version of the core infrastructure (often just the database, kept in sync) runs continuously in the secondary Region; the rest of the stack is provisioned and scaled up only when a failover is triggered.

**Analogy:** the pilot light on a gas stove — a small, always-on flame that can quickly ignite the full burner when needed, rather than lighting one from nothing.

## Warm Standby

A scaled-down but fully functional version of the entire stack runs continuously in the secondary Region, ready to take over and scale up to full capacity on failover.

**Trade-off:** meaningfully faster recovery than Pilot Light, at a meaningfully higher standing cost (you're paying for running infrastructure in two Regions all the time, even if one is under-scaled).

## Multi-Site Active-Active

Full production traffic served from multiple Regions simultaneously (via Route 53 latency or weighted routing); a Region failure simply removes that Region from rotation, with no distinct "failover" event at all.

**Trade-off:** the best RTO/RPO achievable, but the most expensive and operationally complex to run correctly — cross-region data consistency becomes a constant, ongoing engineering concern rather than a one-time failover mechanism.

## Choosing a Tier

The right tier is a business conversation, not a purely technical one: what does an hour of downtime actually cost this specific business, and how does that compare to the standing cost of a warmer strategy? A strategy chosen without that conversation tends to be either wastefully expensive or dangerously under-prepared.

## Senior-Level Considerations

- RTO/RPO targets should be stated explicitly and tested against — "we think we could recover in about an hour" is not the same claim as "we tested a full failover and it took 52 minutes"
- DR strategy is not "set once" — as a system's data volume and dependency graph grow, a Pilot Light strategy that worked at launch can silently become unrealistic (the "light" data sync can't keep up, or the scale-up step now takes far longer than originally measured)
- The failure mode for an untested DR plan isn't "it takes longer than expected" — it's frequently "it doesn't work at all," because untested compensating steps (see the Saga pattern file) or scripts have quietly drifted out of sync with the real production environment
