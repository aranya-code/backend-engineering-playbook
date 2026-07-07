# DNS Failover Architecture

Failover routing (see that file) is the *mechanism*; this file covers the *architecture patterns* built on top of it.

## Active-Passive Failover

```text
Primary Region (active) — serving all traffic
Secondary Region (passive) — idle, scaled down or warm-standby
Route 53 Health Check on Primary
```

If the primary's health check fails, Route 53 failover routing shifts DNS answers to the secondary. This is the simplest DR pattern, but recovery time is bounded by:

1. Health check detection time (quorum + interval)
2. DNS TTL expiry on client/resolver caches
3. However long the secondary needs to actually be ready to serve traffic (if it's not already warm)

## Active-Active with Health-Checked Weighted/Latency Routing

Both regions serve live traffic simultaneously (via weighted or latency routing), each with its own health check. If one region fails, its records are excluded, and 100% of new queries resolve to the surviving region(s) — no explicit "failover event" needed, since it falls out naturally from health-checked routing.

## RTO/RPO Reality Check

DNS failover changes *where new DNS lookups point* — it does nothing for data replication, in-flight session state, or database consistency between regions. A DNS failover architecture is only as good as the data/application layer's own multi-region story underneath it. This is the single most common gap in "we have Route 53 failover so we're covered" claims — DNS is necessary but nowhere near sufficient for DR.

## Practical Recommendations

- Keep TTLs low (60s or less) on records involved in failover, to bound the DNS-layer portion of recovery time
- Test failover regularly — a health check that's misconfigured (wrong path, wrong port, too lenient a threshold) will silently fail to trigger when you actually need it
- Document and monitor the actual end-to-end failover time observed in drills, not just the theoretical TTL-based estimate
