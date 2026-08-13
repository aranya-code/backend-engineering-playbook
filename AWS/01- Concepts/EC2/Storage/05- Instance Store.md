# Instance Store

## Definition

Temporary block storage physically attached to the host machine running the instance — not network storage, and not independent of the instance's own lifecycle the way EBS is.

## Core Characteristics

- **Extremely low latency** — physically local to the host, avoiding any network hop that EBS incurs
- **Ephemeral** — data is lost if the instance stops or terminates, or if the underlying host experiences a hardware failure. A simple **reboot** (not a stop) preserves instance store data, since the instance stays on the same physical host
- **Included in the instance price** — unlike EBS, instance store capacity (where available for a given instance type) is bundled into the instance's hourly cost, not billed separately
- **Not available on every instance type** — it depends entirely on the specific instance type and size; many general-purpose instances have none at all, while storage-optimized (I-series) and some others include substantial local NVMe storage

## Use Cases

- High-speed caching layers where losing the cache on restart is an acceptable, recoverable event (the cache simply rebuilds)
- Temporary scratch space for data processing jobs (sorting, transient intermediate files) that don't need to survive the instance's lifecycle
- Buffer/queue storage in front of load balancers, where durability isn't the point

## EBS vs. Instance Store

| | EBS | Instance Store |
|---|---|---|
| Persistence | Survives stop/reboot | Lost on stop/terminate; survives reboot only |
| Network-attached | Yes | No — physically local |
| Latency | Low (higher than local) | Lowest possible |
| Billing | Separate, by provisioned size/IOPS | Bundled into instance price |
| Availability | Every instance type | Only specific instance types/sizes |
| Best use | Databases, boot volumes, anything needing persistence | Caches, scratch space, ephemeral buffers |

## Senior-Level Considerations

- "Reboots are okay, stops are not" is the detail most often missed — a reboot keeps the instance on the same physical host, so instance store survives it; a stop (and the eventual restart, which may land on different physical hardware entirely) does not
- Any workload using instance store needs an explicit strategy for what happens on data loss — treating it as a durable store because "it's been fine so far" is a latent production risk waiting for the one hardware failure or maintenance event that actually triggers data loss
- Some of the highest-IOPS instance types (certain I-series) are specifically built around fast local NVMe instance store as their primary performance advantage — for genuinely IOPS-bound workloads that can tolerate ephemeral storage (or replicate/rebuild readily), this can meaningfully outperform even io2 Block Express at lower cost
