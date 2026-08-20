# README

## Overview

This section provides a production-oriented troubleshooting reference for Amazon CloudFront.

The guides focus on diagnosing failures and performance problems across the complete request path:

```text
Client
  ↓
CloudFront Edge
  ↓
AWS WAF
  ↓
Cache Behavior
  ↓
Origin
  ↓
ALB / Nginx / Ingress
  ↓
Django / FastAPI / Application
  ↓
Redis / PostgreSQL / External Services
```

CloudFront incidents should be investigated as **distributed request-path problems**, rather than assuming that the edge service is the root cause.

---

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Troubleshooting Methodology](01-%20Troubleshooting%20Methodology.md) | Systematic CloudFront troubleshooting approach and request-path diagnosis. |
| 02 | [403 Forbidden Errors](02-%20403%20Forbidden%20Errors.md) | WAF blocks, signed access failures, restrictions, and authorization issues. |
| 03 | [404 Not Found Errors](03-%20404%20Not%20Found%20Errors.md) | Cache behavior routing, origin path, resource resolution, and missing content. |
| 04 | [502 Bad Gateway Errors](04-%20502%20Bad%20Gateway%20Errors.md) | Origin connectivity, TLS handshake, ALB, and backend reachability failures. |
| 05 | [503 Service Unavailable Errors](05-%20503%20Service%20Unavailable%20Errors.md) | Origin availability, capacity, and upstream failures. |
| 06 | [504 Gateway Timeout Errors](06-%20504%20Gateway%20Timeout%20Errors.md) | Origin latency, timeouts, and slow dependencies. |
| 07 | [High Latency Issues](07-%20High%20Latency%20Issues.md) | Cache performance, origin latency, networking, and backend bottlenecks. |
| 08 | [Low Cache Hit Ratio](08-%20Low%20Cache%20Hit%20Ratio.md) | Cache keys, TTLs, query strings, headers, cookies, and origin load. |
| 09 | [Origin Overload](09-%20Origin%20Overload.md) | Cache misses, traffic amplification, scaling, and backend capacity. |
| 10 | [Signed URL Issues](10-%20Signed%20URL%20Issues.md) | Signature validation, expiration, policies, and resource matching. |
| 11 | [Signed Cookie Issues](11-%20Signed%20Cookie%20Issues.md) | Cookie policies, resource scope, authentication, and authorization. |
| 12 | [TLS and SSL Errors](12-%20TLS%20and%20SSL%20Errors.md) | Viewer certificates, origin TLS, certificates, and handshakes. |
| 13 | [WAF and Access Control Issues](13-%20WAF%20and%20Access%20Control%20Issues.md) | WAF rules, restrictions, authorization, and 403 responses. |
| 14 | [Log Analysis and Diagnostic Workflow](14-%20Log%20Analysis%20and%20Diagnostic%20Workflow.md) | Logs, metrics, correlation, request tracing, and incident workflow. |
| 15 | [Real-World Troubleshooting Scenarios](15-%20Real-World%20Troubleshooting%20Scenarios.md) | Production incidents and end-to-end troubleshooting. |

---

## Troubleshooting Workflow

Use the following sequence for most CloudFront incidents:

```mermaid
flowchart TD
    A[Client Symptom] --> B[Capture Exact Request]
    B --> C[Identify HTTP Status / Latency]
    C --> D{Edge or Origin?}

    D -->|403| E[WAF / Signed Access / Restrictions]
    D -->|404| F[Cache Behavior / Origin / Resource]
    D -->|502| G[Origin Connectivity / TLS / ALB]
    D -->|503| H[Origin Health / Capacity]
    D -->|504| I[Origin Latency / Dependencies]
    D -->|Slow 200| J[Cache / Edge / Origin Latency]
    D -->|Unexpected Content| K[Cache Key / TTL / Authorization]

    E --> L[Correlate Logs and Metrics]
    F --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L

    L --> M[Review Recent Changes]
    M --> N[Form Root-Cause Hypothesis]
    N --> O[Apply Minimal Mitigation]
    O --> P[Validate]
    P --> Q[Document Root Cause]
```

### Core Diagnostic Questions

Before changing configuration, answer:

1. What exact request is failing?
2. What HTTP status or latency is being observed?
3. Which CloudFront cache behavior matches the request?
4. Was the request a cache hit or cache miss?
5. Did AWS WAF allow or block the request?
6. Which origin did CloudFront use?
7. Did the request reach the origin?
8. What did the ALB, Nginx, ingress, or application report?
9. Are PostgreSQL, Redis, Kafka, or external services contributing to the failure?
10. Was there a recent deployment or configuration change?
11. Can the failure be reproduced consistently?
12. Did the mitigation actually restore the complete request path?

---

## HTTP Status Quick Reference

| Status | Typical Investigation Area |
|---|---|
| `403` | WAF, signed URL/cookie, geographic restriction, access control, origin authorization |
| `404` | Cache behavior, incorrect origin, missing resource, routing |
| `502` | Origin connectivity, TLS, ALB, Nginx, application availability |
| `503` | Origin health, capacity, unavailable targets, upstream failures |
| `504` | Origin timeout, slow application, database, external dependency |
| `200` + high latency | Cache miss, origin latency, backend bottleneck |
| `200` + unexpected content | Cache key, TTL, authorization, cache invalidation |

A status code should be treated as an **observation**, not automatically as the root cause.

---

## Request-Path Isolation

A reliable investigation progressively narrows the failure domain:

```text
CloudFront
   │
   ├── Is the distribution deployed?
   │
   ├── Which behavior matches the request?
   │
   ├── Cache hit or miss?
   │
   ├── Did WAF allow it?
   │
   └── Which origin was selected?
            │
            ▼
        Load Balancer
            │
            ├── Target healthy?
            │
            └── Request received?
                    │
                    ▼
                 Nginx / Ingress
                    │
                    ▼
             Django / FastAPI
                    │
             ┌──────┴──────┐
             ▼             ▼
          Redis        PostgreSQL
             │             │
             └──────┬──────┘
                    ▼
             External APIs
```

The objective is to identify the **first failed boundary**.

---

## Evidence to Collect

| Evidence | Purpose |
|---|---|
| Exact URL | Establish reproducible request |
| HTTP method | Distinguish GET, POST, PUT, DELETE behavior |
| Timestamp | Correlate events across systems |
| HTTP status | Classify initial failure |
| Response headers | Identify cache and edge behavior |
| CloudFront metrics | Identify edge-level patterns |
| WAF logs | Identify access-control decisions |
| ALB metrics | Validate origin traffic and latency |
| Nginx logs | Validate request arrival and upstream behavior |
| Application logs | Identify application-level failures |
| Database metrics | Identify backend saturation |
| Redis metrics | Identify cache/session dependency failures |
| Deployment history | Correlate failures with changes |
| CloudFront configuration history | Identify routing/cache-policy regressions |

---

## Production Principles

### Trace the Entire Request Path

Do not stop after finding a CloudFront error.

```text
Symptom
  ↓
CloudFront
  ↓
WAF
  ↓
Cache
  ↓
Origin
  ↓
Application
  ↓
Dependencies
```

### Prefer Evidence Over Assumptions

A statement such as:

```text
"CloudFront is returning 504."
```

describes the symptom.

A stronger diagnosis is:

```text
CloudFront returned 504 because the origin request exceeded the
available response time. Application traces show that PostgreSQL
accounted for most of the request latency after deployment X.
```

### Change the Smallest Possible Surface Area

During an incident, prefer:

- Rolling back one configuration change.
- Correcting one WAF rule.
- Restoring one cache behavior.
- Scaling the affected origin.
- Reverting one deployment.

Avoid broad emergency changes such as:

- Disabling WAF globally.
- Disabling caching globally.
- Invalidating every object unnecessarily.
- Increasing every timeout without identifying the bottleneck.

---

## Security Considerations

CloudFront troubleshooting must not weaken security controls unnecessarily.

Pay particular attention to:

- Signed URLs.
- Signed cookies.
- AWS WAF.
- Origin access controls.
- Authorization headers.
- Cache-key isolation.
- Personalized content.
- Multi-tenant responses.
- Geographic restrictions.

A caching mistake can become a security issue when responses vary by user or tenant but the cache key does not isolate those responses.

---

## Performance Considerations

CloudFront performance depends on both edge configuration and origin architecture.

Monitor the relationship between:

```text
Cache Hit Ratio
      ↓
Origin Request Volume
      ↓
Application Load
      ↓
Database Load
      ↓
Latency
      ↓
Error Rate
```

A drop in cache hit ratio can therefore become an application availability problem.

Similarly, increasing cache efficiency without considering content correctness can create stale-content or authorization problems.

---

## Observability Requirements

A production CloudFront deployment should provide enough telemetry to answer:

```text
What request failed?
Where did it fail?
Why did it fail?
How many users were affected?
When did it start?
What changed?
Did the mitigation work?
```

Useful observability layers include:

- CloudFront metrics and logs.
- AWS WAF logs.
- ALB metrics and access logs.
- Nginx or ingress logs.
- Structured Django/FastAPI logs.
- Distributed traces.
- PostgreSQL metrics.
- Redis metrics.
- Deployment and infrastructure-change history.

Use correlation identifiers where possible so that a request can be followed across application layers.

---

## Recommended Incident Pattern

For production incidents, record:

```text
Incident
├── Impact
├── Detection
├── Timeline
├── Symptoms
├── Evidence
├── Root Cause
├── Contributing Factors
├── Mitigation
├── Permanent Fix
└── Preventive Actions
```

This turns troubleshooting experience into reusable engineering knowledge rather than a one-time operational fix.

## Key Takeaways

- **Troubleshoot CloudFront end-to-end:** follow the request from the edge through WAF, cache behavior, origin infrastructure, application, and dependencies.
- **Use the troubleshooting guides by failure domain:** status codes, latency, caching, access control, TLS, origin health, and diagnostic workflow each require different evidence.
- **Treat caching and security as architectural concerns:** incorrect cache keys, authorization handling, signed access, and WAF rules can affect both reliability and security.
- **Use correlated observability:** CloudFront, WAF, ALB, Nginx, application, database, and deployment telemetry should be analyzed together.
- **Prefer minimal, evidence-based remediation:** isolate the failed layer, mitigate safely, validate the original request, and document the permanent fix.