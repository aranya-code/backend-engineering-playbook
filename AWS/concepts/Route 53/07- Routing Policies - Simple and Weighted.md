# Routing Policies — Simple and Weighted

Route 53 supports seven routing policies. This file covers the two simplest.

## Simple Routing

Routes all traffic to a single resource — no health checking, no logic, just a static answer.

```bash
example.com → EC2 instance
```

**Use case:** a single-server setup with no failover requirement. If you need health checks or multiple values, Simple routing is not the right tool — it has no concept of "unhealthy," it just always answers the same way.

## Weighted Routing

Distributes traffic across multiple resources according to assigned weights.

| Record | Weight | Approx. Traffic Share |
|---|---|---|
| Version A | 80 | 80% |
| Version B | 20 | 20% |

Weights are relative, not absolute percentages — a 4:1 ratio works the same whether the weights are `80/20` or `4/1`. Setting a weight to `0` stops all traffic to that record without deleting it, which is a clean way to pull a version out of rotation temporarily.

**Use cases:**
- **A/B testing** — split traffic between two versions to compare metrics
- **Canary deployments** — send a small percentage (e.g., 5%) to a new version before a full rollout
- **Blue-green deployments** — shift weight gradually from the old (blue) to the new (green) environment

## Senior-Level Considerations

- Weighted routing operates purely at the DNS layer — it has no idea whether a request "succeeded" at the application layer, it only controls *which record a resolver gets back*. Once a client caches that answer for the TTL duration, weighted shifts won't affect that client until the cache expires
- Because of client-side and resolver-side caching, actual observed traffic split can lag or deviate from configured weights, especially with high TTLs or with resolvers that don't fully respect TTL (some corporate/ISP resolvers over-cache)
- Weighted routing is commonly combined with health checks per-record — an unhealthy weighted record is excluded from the pool entirely rather than just getting a "vote of confidence" reduction
