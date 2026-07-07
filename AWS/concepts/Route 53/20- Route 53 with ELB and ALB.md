# Route 53 with ELB / ALB

The standard pattern for routing traffic to a fleet of application servers.

## Architecture

```text
User
 ↓
Route 53
 ↓
Application Load Balancer
 ↓
Target Group → EC2 Instances / ECS Tasks / Lambda
```

## Why Alias Records Matter Here Specifically

Load balancer IP addresses are **not static** and can change — AWS may add, remove, or replace the underlying nodes behind an ALB's DNS name at any time based on scaling and infrastructure maintenance. A plain A record with a hardcoded IP would silently break the moment AWS rotated those addresses. An Alias record avoids this entirely by resolving to the load balancer's current IPs dynamically, server-side, on every query.

## Combining With Health Checks

While the ALB itself already performs target-level health checks (removing unhealthy targets from its own rotation), Route 53 health checks operate one layer up — they can monitor the load balancer's overall endpoint (or a specific health path through it) and drive failover routing to an entirely different region or environment if the whole load balancer becomes unreachable, which is a scenario ALB-level target health checks alone can't address.

## Common Architecture: Multi-Region ALB with Failover

```text
Route 53 Failover Routing
 ├── Primary: ALB in us-east-1  (health-checked)
 └── Secondary: ALB in us-west-2 (health-checked)
```

## Senior-Level Considerations

- Never A-record an ALB's IP addresses directly, even "temporarily" — this is one of the most common sources of mysterious, hard-to-diagnose outages after an AWS-side infrastructure change rotates the load balancer's nodes
- NLBs (Network Load Balancers) *can* have static IPs (via Elastic IPs, one per AZ) — if a use case genuinely requires a fixed IP (some legacy firewall allow-list requirements), NLB is the right tool, not working around ALB's dynamic addressing
