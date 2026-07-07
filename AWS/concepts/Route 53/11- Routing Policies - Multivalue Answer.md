# Routing Policies — Multivalue Answer Routing

Returns up to eight healthy records in response to a single DNS query, letting the client (or its resolver) pick one — a lightweight, DNS-level form of load balancing.

## How It Differs From Simple Routing With Multiple Values

Simple routing can technically hold multiple IP addresses too, but it returns all of them regardless of health. Multivalue Answer routing checks the health of each associated record and **excludes unhealthy ones from the response** — this health awareness is the entire point of the policy.

## Use Cases

- Basic client-side load balancing across multiple EC2 instances without needing a load balancer
- Improving resilience for services that don't warrant a full ALB/NLB

## Senior-Level Considerations

- This is **not** a substitute for a real load balancer — it doesn't do connection draining, weighted distribution, or Layer 7 routing. It's a coarse mechanism: "here are some healthy IPs, you pick"
- Client behavior varies — some clients try all returned IPs in order until one connects, others just use the first, so the "load balancing" effect is inconsistent across different client implementations
- Health check granularity matters: since only *healthy* records are returned, a health check misconfiguration silently shrinks your effective pool without any explicit failover event being visible in the DNS response itself
