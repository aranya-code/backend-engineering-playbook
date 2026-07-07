# Routing Policies — Failover Routing

A primary/secondary (active/passive) configuration: traffic goes to the primary resource as long as it's healthy, and automatically shifts to the secondary if the primary's health check fails.

## Flow

```text
Is Primary Healthy?
   YES → Route to Primary
   NO  → Route to Secondary
```

## Requirements

- A health check **must** be associated with the primary record — failover routing has no concept of "unhealthy" without one
- Both a Primary and a Secondary record must exist in the same hosted zone with the same name and type

## Use Cases

- Disaster recovery (DR) — standby environment in a second region
- High availability — automatic failover without manual DNS changes or human intervention at 3am

## Senior-Level Considerations

- Failover routing is DNS-layer failover, not connection-layer failover — an in-flight TCP connection to the primary won't be rerouted; only *new* DNS lookups after the TTL expires will get the secondary's answer. This means actual failover time is bounded by TTL, not instantaneous
- A secondary record can (and often should) also have its own health check — a "healthy secondary" check is a common safeguard so you don't fail over into a broken standby
- Failover routing pairs naturally with **DNS Failover Architecture** patterns (see that file) covering full active-passive and active-active designs, and it's frequently combined with database replication strategy — DNS failover only helps if the secondary region actually has usable data
