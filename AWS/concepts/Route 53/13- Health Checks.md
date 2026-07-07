# Health Checks

Route 53 health checks continuously monitor the health of an endpoint and feed that status into routing decisions (failover, weighted, multivalue) in near real time.

## How They Work

```bash
https://myapp.com/health
```

Route 53 checkers — distributed across multiple global locations — request this endpoint on a defined interval. If enough checkers report failure, the endpoint is marked unhealthy, and:

- It's removed from Multivalue Answer responses
- Failover routing shifts to the secondary
- Weighted/latency records associated with it are skipped in favor of remaining healthy records

## Health Check Types

| Type | Checks |
|---|---|
| HTTP | Plain HTTP endpoint returns a 2xx/3xx status |
| HTTPS | Same, over TLS — note this does **not** validate the certificate itself |
| TCP | A successful TCP handshake on the given port (no application-layer check) |
| Calculated | Combines the status of multiple other health checks with AND/OR/NOT logic |
| CloudWatch Alarm | Tracks the state of a CloudWatch alarm instead of probing an endpoint directly |

## Calculated Health Checks

A calculated health check lets you express logic like "healthy only if at least 2 of these 3 regional checks are healthy" — useful for avoiding a single flaky check from triggering a full failover, or for requiring multiple independent signals (e.g., both an app-layer check and a database connectivity check) to agree before declaring an outage.

## Determining "Unhealthy" — Quorum

A single checker failing doesn't immediately mark an endpoint unhealthy. Route 53 uses a quorum across its distributed checker fleet (by default, 18 checkers globally, needing a majority to agree) specifically to avoid false positives from a transient regional network issue between one checker location and your endpoint.

## Senior-Level Considerations

- Health checks against endpoints **outside AWS** (e.g., an on-prem server) are fully supported — Route 53 health checking isn't AWS-resource-specific
- Health check frequency (standard: 30s, fast: 10s) directly trades off "how quickly can I detect and fail over" against "how much load do health checks themselves add to my endpoint," which matters for low-traffic or rate-limited backends
- A common production mistake: pointing the health check at `/` instead of a dedicated `/health` endpoint that actually verifies downstream dependencies (database, cache, etc.) — a plain `/` check can return 200 even when the app is functionally broken
