# Resilience Patterns — Circuit Breaker and Bulkhead

## The Problem: Cascading Failure

If Service A calls Service B, and B becomes slow (not down — just slow), A's requests to B start piling up, consuming A's threads/connections while waiting. Eventually A itself becomes unresponsive to its own callers, even though A's own code has no bug. The failure cascades outward from B to everything upstream of it.

## Circuit Breaker

Wraps a call to a dependency and tracks its recent failure rate. Once failures cross a threshold, the breaker "opens" — further calls fail immediately (or return a fallback) without even attempting the network call, for a cooldown period. After the cooldown, it allows a limited number of trial requests through ("half-open") to check if the dependency has recovered.

```text
CLOSED (normal) → too many failures → OPEN (fail fast) → cooldown expires → HALF-OPEN (test) → success → CLOSED
                                                                                    ↓ failure
                                                                                   OPEN
```

## Why This Is Different From Retries

Retries help with a single transient failure. A circuit breaker helps when the dependency is *persistently* unhealthy — at that point, retrying just adds more load to an already-struggling service and wastes the caller's own resources waiting. The circuit breaker's whole point is to **stop trying** for a while, deliberately.

## Where AWS Fits

AWS doesn't provide a managed "circuit breaker" service — this is an application-layer pattern, typically implemented via a library (e.g., resilience4j on the JVM, or similar patterns in application code) running inside your ECS/EKS/Lambda workload. AWS App Mesh and service-mesh sidecars (e.g., Envoy) can implement circuit breaking at the infrastructure layer without application code changes, which is a common reason teams adopt a service mesh at scale.

## Bulkhead Pattern

Named after ship compartments designed so that one compartment flooding doesn't sink the whole ship. In software: isolating resources (thread pools, connection pools) per dependency, so a slowdown in one dependency can't exhaust the resources needed to call a completely unrelated dependency.

**Example:** if Service A calls both a payments API and a recommendations API from a shared thread pool, a slow recommendations API can starve the pool and block payment calls too — even though payments has nothing to do with the slowness. Separate pools per dependency prevent this.

## Senior-Level Considerations

- A circuit breaker's fallback behavior matters as much as the breaker itself — failing fast with a clear error is very different from failing fast with a confusing one, and a good fallback (cached data, a degraded-but-functional response) is often the actual point
- Bulkheads have a real cost: dedicating separate resource pools per dependency means some pools sit partially idle while others could theoretically use that capacity — it's a deliberate trade of efficiency for isolation
- Both patterns assume you can detect "unhealthy" quickly and accurately — a circuit breaker with a badly tuned threshold can trip on normal variance (false positives) or fail to trip during a real outage (false negatives)
