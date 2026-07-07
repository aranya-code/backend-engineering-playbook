# Advantages and Limitations of Route 53

## Advantages

### 100% Availability SLA
One of the few AWS services with a 100% (not 99.9-something) SLA, underpinned by the global anycast architecture and shuffle sharding.

### Deep AWS Integration
Alias records, health checks, and routing policies are purpose-built to work seamlessly with ALB, CloudFront, S3, and API Gateway — far less friction than managing DNS for AWS resources through a third-party provider.

### Flexible Routing
Seven distinct routing policies cover nearly every traffic-shaping need (simple failover, geo-based compliance routing, latency optimization, gradual weighted rollouts) without needing external tooling.

### Global Anycast Network
Consistently fast resolution worldwide, with resilience against regional network issues baked into the architecture itself.

### Registrar + DNS in One Place
Domain registration and DNS hosting can be managed together, simplifying operations for teams that don't want to juggle a separate registrar relationship.

## Limitations

### Cost at Very High Query Volume
Per-query pricing (even though individually cheap) can add up meaningfully for extremely high-traffic public hosted zones compared to some flat-rate DNS providers.

### Alias Records Are AWS-Specific
Alias behavior only applies within Route 53 — you can't get equivalent zone-apex flexibility on another DNS provider without workarounds, which is a lock-in consideration if you ever need to migrate DNS away from AWS.

### DNS-Layer Failover Isn't True High Availability
As covered in DNS Failover Architecture, TTL-bound DNS failover is not equivalent to instantaneous, connection-aware failover — it's necessary but not sufficient for a real DR story.

### Geoproximity/Traffic Flow Complexity
The more advanced routing configurations (geoproximity bias, multi-layer Traffic Flow policies) have a real learning curve and are easy to misconfigure without careful testing.

### No Built-In WAF-Style Request Inspection
Route 53 operates at the DNS layer only — it has no visibility into HTTP request content. Content-based routing or filtering requires a layer above it (CloudFront + WAF, or an ALB).

## Senior-Level Takeaway

Route 53 is excellent at what it's scoped to do — authoritative DNS, health-check-driven routing, and registrar functions — but it's one layer in a larger availability and security architecture, not a complete solution on its own.
