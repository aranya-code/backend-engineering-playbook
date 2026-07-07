# Route 53 vs Other DNS Solutions

## Overview

Route 53 competes with both third-party DNS providers and AWS's own load-balancing services, which serve different (if overlapping) purposes.

## Route 53 vs Cloudflare DNS / Third-Party DNS

| | Route 53 | Cloudflare DNS |
|---|---|---|
| AWS resource integration | Native (Alias records) | Requires CNAME workarounds, extra lookup |
| Pricing model | Per-hosted-zone + per-query | Free tier available, paid tiers for advanced features |
| Global network | AWS anycast | Cloudflare's own anycast (also very large) |
| Extra features | Route 53 Resolver, deep AWS routing policies | Built-in CDN, WAF, and DDoS protection bundled by default |
| Best fit | AWS-centric infrastructure | Multi-cloud or CDN-first setups |

## Route 53 vs Load Balancer (ALB/NLB)

| Route 53 | Load Balancer |
|---|---|
| DNS resolution — answers "which IP to connect to" | Traffic distribution — handles the actual connections |
| Global, cross-region routing | Regional (or AZ-level) request handling |
| Operates at the DNS layer | Operates at Layer 4 (NLB) or Layer 7 (ALB) |
| Failover bounded by TTL | Failover near-instantaneous, connection-aware |

These aren't substitutes — a well-designed architecture typically uses **both**: Route 53 to route users to the right region/environment, and a load balancer within that region to distribute traffic across instances.

## Route 53 vs CloudTrail vs CloudWatch

A distinction worth being explicit about, since these three are easy to conflate:

- **Route 53** — DNS resolution and traffic routing
- **CloudTrail** — audit log of API calls made *against* AWS accounts (including calls to Route 53 itself, like who created or changed a record)
- **CloudWatch** — metrics, logs, and alarms (used *to monitor* Route 53 health checks and query volume)

## When to Choose What

- **AWS-heavy environment, need deep integration** → Route 53
- **Need CDN + WAF + DNS bundled, multi-cloud flexibility** → third-party like Cloudflare
- **Need to distribute traffic within a region across instances** → that's a load balancer's job, not DNS's
