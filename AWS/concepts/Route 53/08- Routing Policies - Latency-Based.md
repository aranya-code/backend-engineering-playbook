# Routing Policies — Latency-Based Routing

Routes users to the AWS Region that gives them the lowest network latency — not necessarily the geographically closest region, since latency and geographic distance don't always correlate (network topology, undersea cable routes, and peering agreements all matter more than straight-line distance).

## Example

| User Location | Routed Region |
|---|---|
| India | Mumbai (ap-south-1) |
| USA | N. Virginia (us-east-1) |
| Europe | Frankfurt (eu-central-1) |

## How It Works

AWS maintains latency measurements between its edge network and broad internet IP ranges. When a latency-based query comes in, Route 53 compares the requester's inferred location against its latency data for each region where you've created a latency record, and returns the lowest-latency option.

## Benefits

- Lower perceived latency for global user bases
- No manual geo-mapping required — AWS's latency data handles the routing logic

## Senior-Level Considerations

- Latency routing is based on the *resolver's* location, not necessarily the end user's — if a user is behind a resolver in a different region than themselves (common with some public DNS providers or corporate VPNs), the routing decision reflects the resolver's location, not the user's
- Combine with health checks so a "lowest latency" region that happens to be unhealthy is automatically excluded — otherwise latency routing will happily route users straight into an outage
- Latency routing answers "which region is fastest," not "which region is healthy" — it's a routing-optimization tool, not a failover tool on its own
