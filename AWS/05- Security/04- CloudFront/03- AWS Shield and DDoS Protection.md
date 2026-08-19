# 03- AWS Shield and DDoS Protection

## Overview

AWS Shield is AWS's managed Distributed Denial of Service (DDoS) protection service. It is designed to protect internet-facing AWS resources against attacks that attempt to exhaust network, transport, or application-layer capacity.

For CloudFront architectures, DDoS protection is part of a broader layered security model:

```text
Internet
   │
   │ DDoS traffic
   ▼
┌──────────────────────┐
│    AWS Edge Layer    │
│                      │
│ CloudFront + Shield  │
│        + WAF         │
└──────────┬───────────┘
           │
           │ Filtered traffic
           ▼
┌──────────────────────┐
│ Load Balancer / API  │
│ Gateway / Origin     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Django / FastAPI /   │
│ Microservices        │
└──────────────────────┘
```

The important architectural distinction is that **Shield, WAF, and CloudFront solve different problems**:

| Service | Primary responsibility |
|---|---|
| CloudFront | Global edge delivery, caching, TLS termination, origin shielding |
| AWS Shield Standard | Baseline DDoS protection for supported AWS services |
| AWS Shield Advanced | Enhanced DDoS protection, visibility, response capabilities, and cost protection features |
| AWS WAF | Application-layer HTTP request filtering |
| Origin | Application and business logic |

A production architecture should therefore avoid treating "DDoS protection" as a single switch. Network-level protection, HTTP filtering, caching, rate limiting, origin isolation, observability, and incident response all contribute to the overall defense.

## What Is a DDoS Attack?

A Distributed Denial of Service attack attempts to make a service unavailable by overwhelming it with traffic or resource-consuming requests.

The traffic can originate from many distributed systems:

```text
Attacker infrastructure
   ├── Host A
   ├── Host B
   ├── Host C
   ├── Host D
   └── ...
          │
          ▼
      Internet
          │
          ▼
      Target
```

The attack does not necessarily require a sophisticated application exploit. The objective may simply be to consume enough capacity that legitimate clients cannot successfully use the service.

## DDoS Attack Layers

DDoS attacks can target different layers of the networking stack.

| Layer | Example | Primary resource targeted |
|---|---|---|
| Network | UDP flood | Network bandwidth |
| Network | IP protocol flood | Network infrastructure |
| Transport | SYN flood | TCP connection capacity |
| Transport | TCP/UDP flood | Connection or network capacity |
| Application | HTTP request flood | Application CPU, memory, workers, databases |
| Application | Expensive endpoint abuse | Backend compute and database capacity |

The distinction is important because increasing bandwidth does not necessarily solve an application-layer attack.

For example:

```text
GET /search?q=...
```

may be syntactically valid HTTP traffic but still be expensive if the endpoint performs:

```text
HTTP request
    │
    ▼
Django/FastAPI
    │
    ▼
Complex query
    │
    ▼
PostgreSQL
    │
    ▼
Large result set
```

A large volume of legitimate-looking requests can exhaust the origin even when the network infrastructure itself remains healthy.

## AWS Shield

AWS Shield provides managed DDoS protection for AWS workloads.

There are two primary protection tiers:

| Capability | Shield Standard | Shield Advanced |
|---|---|---|
| Baseline DDoS protection | Yes | Yes |
| Automatic protection for supported AWS services | Yes | Yes |
| Enhanced detection and mitigation | Limited | Yes |
| Advanced visibility | Limited | Yes |
| DDoS response assistance | No equivalent to Advanced response capabilities | Yes |
| DDoS cost protection features | No | Yes |
| Advanced operational support | No | Yes |

Shield Standard is included automatically for eligible AWS services at no additional charge.

Shield Advanced is intended for organizations with higher availability requirements, significant internet exposure, or a stronger need for DDoS visibility, response, and cost protection.

## Shield Standard

Shield Standard provides baseline protection against common network and transport-layer DDoS attacks.

CloudFront is one of the AWS services protected by Shield Standard.

This means a CloudFront-based application already benefits from AWS-managed infrastructure-level DDoS protection without requiring the application team to build a packet-level DDoS mitigation system.

The architecture is conceptually:

```text
Internet
   │
   ▼
AWS Edge Infrastructure
   │
   ├── DDoS detection / mitigation
   │
   ▼
CloudFront
   │
   ▼
Origin
```

### When Shield Standard Is Appropriate

Shield Standard is generally sufficient when:

- The workload has normal public-internet exposure.
- The business does not require enhanced DDoS operational support.
- Advanced DDoS visibility is not a requirement.
- The organization accepts AWS's baseline DDoS protection model.

It should still be combined with CloudFront caching, WAF controls, secure origins, and application-level protections.

## Shield Advanced

Shield Advanced provides additional capabilities for workloads where DDoS attacks represent a significant operational or financial risk.

Typical reasons to consider it include:

- Business-critical public applications.
- High-volume internet-facing APIs.
- Financially sensitive workloads.
- Critical SaaS platforms.
- Applications with strict availability requirements.
- Organizations requiring enhanced DDoS visibility.
- Organizations requiring access to AWS DDoS response resources.
- Workloads where scaling-related DDoS costs are a concern.

Shield Advanced is not simply "Shield Standard with more traffic capacity." Its value is primarily in enhanced detection, visibility, operational response, and protection mechanisms around serious DDoS events.

## CloudFront as a DDoS Absorption Layer

CloudFront changes the architecture of a public application by placing AWS's global edge network between clients and the origin.

Without CloudFront:

```text
Internet
   │
   ├──────────────► Origin
   ├──────────────► Origin
   ├──────────────► Origin
   └──────────────► Origin
```

With CloudFront:

```text
Internet
   │
   ▼
CloudFront Edge
   │
   ├── Cache hit ─────────────► Response
   │
   └── Cache miss
             │
             ▼
           Origin
```

This provides an important architectural property: many requests can be served without reaching the origin.

For cacheable content:

```text
10,000 requests
      │
      ▼
CloudFront
      │
      ├── 9,900 cache hits
      │
      └── 100 origin requests
```

The exact ratio depends on the workload and cache configuration, but the principle is fundamental.

## Why Caching Matters for DDoS Resilience

Caching is not a replacement for DDoS protection, but it can substantially reduce origin exposure.

Consider:

```text
Attacker
   │
   │ 100,000 requests
   ▼
CloudFront
   │
   ├── Cached requests ──► Edge response
   │
   └── Uncached requests ──► Origin
```

If attackers request highly cacheable objects, CloudFront can serve many responses at the edge.

If attackers target uncached dynamic endpoints, the origin may still receive a large number of requests.

Therefore:

> DDoS resilience depends heavily on whether the attack traffic can force expensive origin work.

## Shield vs WAF

Shield and AWS WAF operate at different security layers.

### Shield

Shield primarily addresses DDoS attacks against network and transport infrastructure and provides additional capabilities through Shield Advanced.

### WAF

WAF evaluates HTTP requests and can apply application-aware rules.

For example:

```text
POST /login
POST /login
POST /login
POST /login
...
```

A WAF rule or rate-based control can help identify and restrict abusive request patterns.

The combined architecture is:

```mermaid
flowchart LR
    I[Internet]
    S[AWS Shield]
    C[CloudFront]
    W[AWS WAF]
    O[Origin]
    A[Django / FastAPI]

    I --> S
    S --> C
    C --> W
    W --> O
    O --> A
```

The exact internal processing order should be understood from the current AWS service architecture and configured protections, but architecturally the services form complementary layers rather than substitutes.

## Shield vs WAF vs CloudFront

| Capability | CloudFront | Shield | WAF |
|---|---|---|---|
| CDN | Yes | No | No |
| Edge caching | Yes | No | No |
| TLS termination | Yes | No | No |
| Network DDoS protection | Integrated with AWS protection | Yes | No |
| HTTP request inspection | Limited through configuration | Not its primary purpose | Yes |
| IP blocking | Through WAF integration | Not its primary purpose | Yes |
| Rate-based HTTP controls | Through WAF | Not its primary purpose | Yes |
| SQL injection rules | No | No | Yes |
| Bot controls | No | No | Yes |
| Origin shielding | Yes | No | No |
| DDoS operational response | No | Shield Advanced | No |

## Layered DDoS Architecture

A production CloudFront application should use defense in depth.

```mermaid
flowchart TB
    I[Internet]

    D[DDoS Protection<br/>AWS Shield]
    C[CloudFront<br/>Edge + Cache]
    W[AWS WAF<br/>HTTP Filtering]
    L[ALB / API Gateway]
    O[Application Origin]
    DB[(PostgreSQL)]
    R[(Redis)]

    I --> D
    D --> C
    C --> W
    W --> L
    L --> O
    O --> DB
    O --> R
```

Each layer addresses different failure modes.

| Layer | Primary goal |
|---|---|
| Shield | Absorb and mitigate DDoS infrastructure attacks |
| CloudFront | Terminate connections at the edge and reduce origin traffic |
| WAF | Filter malicious or abusive HTTP requests |
| ALB | Distribute application traffic |
| Application | Authenticate, authorize, validate, and enforce business rules |
| Redis | Reduce repeated expensive backend operations where appropriate |
| PostgreSQL | Persist application data |

## Application-Layer DDoS

The most important senior-level distinction is between volumetric DDoS and application-layer resource exhaustion.

A request such as:

```http
GET /health
```

may be cheap.

A request such as:

```http
GET /reports/monthly?customer_id=...
```

may trigger:

```text
API
 │
 ├── Authentication
 ├── Authorization
 ├── PostgreSQL joins
 ├── Aggregations
 ├── Redis access
 └── Serialization
```

An attacker does not necessarily need massive bandwidth if every request consumes substantial backend resources.

Therefore, backend engineers should identify expensive endpoints and protect them independently.

## Protecting Expensive APIs

For Django or FastAPI APIs, consider:

- Authentication requirements.
- Authorization.
- WAF rules.
- Rate-based controls.
- Request size limits.
- Pagination limits.
- Query complexity limits.
- Timeouts.
- Database connection limits.
- Caching.
- Redis-backed throttling where appropriate.
- Application-level quotas.

For example:

```text
Public static content
        │
        ▼
   CloudFront cache

Authenticated API
        │
        ▼
       WAF
        │
        ▼
   Rate controls
        │
        ▼
     Backend
```

Do not rely exclusively on application workers to absorb abusive traffic.

## Rate Limiting

Rate limiting controls how frequently clients can make requests.

For example:

```text
Client A
  │
  ├── Request 1
  ├── Request 2
  ├── Request 3
  └── Request 4
```

A rate policy may allow only a bounded request rate over a defined evaluation window.

Rate limiting is particularly useful for:

- Login endpoints
- Password reset
- Search
- Expensive reports
- Public APIs
- Authentication APIs
- Resource creation endpoints

### WAF Rate-Based Controls

CloudFront can be integrated with AWS WAF rate-based rules.

Conceptually:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
WAF rate-based rule
  │
  ├── Normal traffic ──► Origin
  │
  └── Excessive traffic ──► Block / challenge / control
```

The exact rule behavior should be designed around the application's traffic patterns.

A rate threshold that is too low can block legitimate clients during traffic spikes.

A threshold that is too high may provide little protection.

## Origin Protection

CloudFront should prevent clients from bypassing the edge and directly reaching the origin where practical.

Consider:

```text
Preferred:

Internet
   │
   ▼
CloudFront
   │
   ▼
Origin

Avoid:

Internet ───────► CloudFront
   │
   └─────────────► Origin
```

If the origin is publicly reachable, an attacker may bypass:

- CloudFront caching
- WAF controls attached to CloudFront
- Edge-level protections
- Origin traffic optimization

This can undermine the architecture.

## Protecting an ALB Origin

A common architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
AWS WAF
   │
   ▼
Application Load Balancer
   │
   ▼
ECS / EKS / EC2
   │
   ▼
Django / FastAPI
```

The origin should be configured so that it is not treated as an unrestricted public API endpoint.

Origin access restrictions can be implemented using mechanisms appropriate to the origin type and architecture.

For CloudFront distributions, origin authentication and access controls should be designed so that only expected CloudFront traffic can reach protected origins where supported.

## CloudFront and S3

For static or private S3 content, CloudFront can sit in front of S3.

A modern architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
S3
```

For private S3 origins, CloudFront Origin Access Control (OAC) is generally preferred over making the bucket publicly readable.

The desired security model is:

```text
Internet
   │
   X  Direct S3 access denied
   │
   ▼
CloudFront
   │
   │ Authorized origin request
   ▼
S3
```

This prevents attackers from bypassing CloudFront to retrieve protected objects directly from S3.

## DDoS and Microservices

A microservice architecture can amplify the impact of application-layer attacks.

For example:

```text
Attacker
   │
   ▼
API
   │
   ├── User Service
   ├── Order Service
   ├── Payment Service
   ├── Inventory Service
   └── Notification Service
```

One public endpoint can trigger work across multiple internal services.

This can create a cascading failure:

```text
HTTP flood
    │
    ▼
API workers exhausted
    │
    ▼
Service retries increase
    │
    ▼
Internal traffic increases
    │
    ▼
Database connections exhausted
    │
    ▼
System-wide degradation
```

DDoS resilience therefore includes controlling internal amplification.

Useful controls include:

- Timeouts.
- Circuit breakers.
- Bounded retries.
- Queue-based workloads.
- Bulkheads.
- Connection pool limits.
- Backpressure.
- Idempotency.
- Caching.

## Celery and Asynchronous Work

Expensive operations should not always execute synchronously inside the request path.

For example:

```text
HTTP request
    │
    ▼
API
    │
    ├── Validate
    ├── Persist job
    └── Queue task
             │
             ▼
           Celery
             │
             ▼
         Worker pool
```

This can prevent request workers from being consumed by long-running tasks.

However, asynchronous processing does not automatically solve DDoS.

An attacker can still generate:

```text
100,000 HTTP requests
       │
       ▼
100,000 queued tasks
```

The queue can become the new bottleneck.

Therefore:

- Limit task creation.
- Apply quotas.
- Validate requests before enqueueing.
- Use bounded concurrency.
- Monitor queue depth.
- Reject or defer excess work.

## Redis and DDoS Protection

Redis can be useful for application-level rate limiting and short-lived counters.

A conceptual pattern is:

```text
Request
   │
   ▼
API
   │
   ▼
Redis counter
   │
   ├── Within limit ──► Continue
   │
   └── Exceeded ──────► Reject
```

Redis should not be treated as the primary DDoS mitigation layer.

A sufficiently large attack can itself overwhelm the application before requests reach the Redis-based control logic.

Use edge-level protections first, then application-level controls for finer-grained behavior.

## Caching Strategy During Attacks

Caching can reduce origin load significantly, but only when the requests are cacheable.

Consider:

```text
Attack A:
GET /static/app.js

Attack B:
GET /api/orders?user_id=123
```

Attack A may be served from CloudFront cache.

Attack B may require application execution.

Therefore, identify:

- Static resources.
- Public cacheable APIs.
- Dynamic APIs.
- Personalized responses.
- Authentication-dependent content.

Avoid accidentally caching personalized or sensitive responses.

## Cache Key Design and DDoS

Poor cache-key design can increase origin load.

For example:

```text
/api/products?id=1
/api/products?id=2
/api/products?id=3
...
```

may produce many unique cache entries.

More importantly, attackers may deliberately vary cache-key inputs:

```text
/api/products?random=1
/api/products?random=2
/api/products?random=3
...
```

If those query parameters participate in the cache key, every request may become a cache miss.

The result can be:

```text
Attack traffic
      │
      ▼
CloudFront
      │
      │ cache miss
      ▼
Origin
      │
      ▼
Database
```

Cache-key design is therefore both a performance concern and a resilience concern.

## DDoS and Origin Shielding

CloudFront can reduce origin pressure by consolidating requests through the edge infrastructure.

For high-scale workloads, CloudFront Origin Shield can provide an additional centralized caching layer between CloudFront edge locations and the origin.

Conceptually:

```text
Viewer
  │
  ▼
CloudFront Edge
  │
  ▼
Origin Shield
  │
  ▼
Origin
```

Origin Shield can be useful when:

- The origin is expensive to reach.
- Multiple edge locations generate cache misses.
- The workload has high global traffic.
- The origin benefits from request consolidation.

It is not a replacement for Shield or WAF.

## High Availability

DDoS protection should be part of a broader high-availability design.

A typical architecture is:

```text
                    Internet
                       │
                       ▼
              CloudFront + Shield
                       │
                       ▼
                      WAF
                       │
                       ▼
                 Load Balancer
                       │
              ┌────────┴────────┐
              ▼                 ▼
          AZ / Node          AZ / Node
              │                 │
              └────────┬────────┘
                       ▼
                 Application
                       │
              ┌────────┴────────┐
              ▼                 ▼
           Redis            PostgreSQL
```

The goal is to prevent a single component from becoming the failure point.

DDoS protection cannot compensate for:

- A single application instance.
- A single database failure domain.
- Unbounded worker pools.
- Uncontrolled retries.
- A single Redis node where availability is critical.
- A publicly exposed origin that bypasses edge controls.

## Monitoring

DDoS resilience requires observability.

Monitor at least:

### CloudFront

- Requests.
- Bytes downloaded.
- Cache hit ratio.
- HTTP status distribution.
- Origin request count.
- Error rates.
- Geographic traffic patterns.

### WAF

- Allowed requests.
- Blocked requests.
- Rule matches.
- Rate-based rule activity.
- Bot-related detections where enabled.

### Origin

- CPU.
- Memory.
- Request latency.
- Worker utilization.
- Connection count.
- Database connections.
- Redis operations.
- Queue depth.
- HTTP 5xx rates.

### Business Metrics

Technical metrics alone may not reveal impact.

Also monitor:

- Login failures.
- Checkout failures.
- API success rates.
- Order processing latency.
- Payment failures.
- Customer-facing availability.

## Detecting an Attack

A DDoS event often produces multiple simultaneous signals.

For example:

```text
CloudFront requests       ↑↑↑
WAF blocked requests      ↑↑↑
Origin requests           ↑
Origin CPU                ↑↑
Database connections      ↑↑
API latency               ↑↑
Error rate                ↑↑
```

A traffic increase alone does not prove a DDoS attack.

A legitimate product launch can produce similar traffic patterns.

Investigate:

- Source distribution.
- Request paths.
- User-agent patterns.
- HTTP methods.
- Cache hit ratio.
- Geographic distribution.
- Authentication behavior.
- WAF rule matches.
- Origin resource utilization.

## Logging

CloudFront and WAF logs can provide useful forensic information.

A useful incident investigation sequence is:

```text
Traffic spike
    │
    ▼
CloudFront metrics
    │
    ▼
WAF metrics / logs
    │
    ▼
Origin metrics
    │
    ▼
Application logs
    │
    ▼
Database / Redis metrics
```

Correlating these layers is more useful than inspecting application logs in isolation.

## AWS Shield Advanced Operational Model

Shield Advanced is particularly valuable for organizations that require stronger operational support around DDoS events.

Important considerations include:

- Protected resource configuration.
- DDoS visibility.
- Detection and mitigation telemetry.
- Incident response procedures.
- AWS Support integration.
- Cost protection capabilities.
- Coordination with AWS WAF.

Organizations should not purchase Shield Advanced without defining what additional operational requirements it is expected to satisfy.

The correct question is:

> What risk does Shield Advanced reduce that our baseline CloudFront + Shield Standard + WAF architecture does not adequately address?

## Cost Considerations

DDoS protection has both direct and indirect cost implications.

A successful attack can increase:

- CloudFront request volume.
- Origin compute usage.
- Load balancer processing.
- Database workload.
- Data transfer.
- Logging volume.
- Autoscaling activity.

A resilient architecture aims to stop expensive work as early as possible:

```text
Internet
   │
   ▼
Shield
   │
   ▼
CloudFront cache
   │
   ▼
WAF
   │
   ▼
Origin
   │
   ▼
Database
```

The farther malicious traffic travels into the architecture, the more expensive it can become.

Shield Advanced includes DDoS cost protection capabilities intended to help qualifying customers with certain scaling-related charges caused by DDoS attacks.

Organizations should understand the current AWS eligibility, coverage, and claim requirements before treating this as a guaranteed reimbursement mechanism.

## Incident Response

A DDoS runbook should be prepared before an incident.

A practical response sequence is:

1. Confirm whether traffic is legitimate or anomalous.
2. Check CloudFront request and error metrics.
3. Inspect WAF blocked and allowed requests.
4. Identify affected URLs and methods.
5. Check origin CPU, memory, connections, and latency.
6. Determine whether traffic is reaching the origin.
7. Tighten WAF controls if appropriate.
8. Protect expensive endpoints.
9. Verify that legitimate clients remain functional.
10. Escalate to AWS support or Shield Advanced response capabilities when appropriate.
11. Preserve logs and metrics for post-incident analysis.
12. Review and improve controls after the incident.

Avoid making uncontrolled changes during an active attack.

A WAF rule that blocks too aggressively can convert a DDoS incident into an availability incident caused by your own mitigation.

## Disaster Recovery

DDoS protection and disaster recovery solve different problems.

Shield can help mitigate attacks, but it does not recover an application from:

- Data corruption.
- Application deployment failures.
- Database destruction.
- Regional infrastructure failures.
- Incorrect configuration.
- Permanent data loss.

A resilient system should therefore combine:

```text
DDoS Protection
       +
High Availability
       +
Backups
       +
Multi-AZ
       +
Multi-Region where justified
       +
Infrastructure as Code
       +
Incident Response
```

For multi-region systems, CloudFront can provide a global edge layer while DNS, origin groups, application routing, or other AWS mechanisms determine regional failover.

## Common Mistakes and Pitfalls

### Treating Shield as a Complete Security Solution

**Problem:** The team assumes Shield protects every application-layer attack.

**Why it happens:** Network-level DDoS protection and HTTP abuse are different problems.

**Correction:** Combine Shield with WAF, caching, authentication, rate limiting, and application-level controls.

### Exposing the Origin Directly

**Problem:** Attackers bypass CloudFront and WAF.

**Correction:** Restrict direct origin access where practical and design the origin to trust the intended CloudFront path.

### Assuming CloudFront Caching Protects Dynamic APIs

**Problem:** Dynamic requests continue reaching the backend.

**Correction:** Analyze cacheability and protect dynamic endpoints independently.

### Using Only Application-Level Rate Limiting

**Problem:** The application may already be overloaded before its rate limiter executes.

**Correction:** Push coarse-grained protection toward the edge and use application controls for finer-grained quotas.

### Creating Unlimited Celery Tasks

**Problem:** HTTP traffic is converted into queue pressure.

**Correction:** Bound task creation, enforce quotas, monitor queue depth, and reject excess work.

### Using Unbounded Retries

**Problem:** A DDoS or backend failure becomes amplified by retries.

**Correction:** Use bounded retries, exponential backoff, jitter, and circuit-breaking patterns.

### Blocking Legitimate Traffic During an Attack

**Problem:** An emergency WAF rule causes collateral damage.

**Correction:** Start with narrowly scoped rules and observe metrics before broadening them.

### Ignoring Cache-Key Manipulation

**Problem:** Attackers vary query parameters to create cache misses.

**Correction:** Review cache-key configuration and exclude irrelevant parameters from the cache key where safe.

### Assuming More Autoscaling Solves DDoS

**Problem:** Autoscaling may simply increase infrastructure consumption.

**Correction:** Stop malicious or abusive traffic before expensive backend work whenever possible.

### Ignoring Origin Protection

**Problem:** Direct-origin traffic bypasses the intended edge security architecture.

**Correction:** Make origin access part of the threat model and explicitly protect the origin.

## Production Architecture Example

A production API architecture can look like:

```mermaid
flowchart TB
    U[Internet Clients]

    S[AWS Shield]
    CF[CloudFront]
    W[AWS WAF]
    ALB[Application Load Balancer]

    EKS[EKS / ECS / EC2]
    API[Django / FastAPI]
    R[(Redis)]
    DB[(PostgreSQL)]
    K[Kafka]
    C[Celery Workers]

    U --> S
    S --> CF
    CF --> W
    W --> ALB
    ALB --> EKS
    EKS --> API

    API --> R
    API --> DB
    API --> K
    K --> C
    C --> DB
```

The protection strategy is layered:

```text
Shield
  │
  ├── Network / transport DDoS resilience
  │
CloudFront
  │
  ├── Edge termination
  ├── Caching
  └── Traffic absorption
  │
WAF
  │
  ├── HTTP filtering
  ├── Rate-based controls
  └── Application-aware rules
  │
Application
  │
  ├── Authentication
  ├── Authorization
  ├── Quotas
  └── Validation
  │
Backend
  │
  ├── Timeouts
  ├── Backpressure
  ├── Circuit breakers
  └── Bounded resources
```

## Architecture Decision Matrix

| Scenario | CloudFront | Shield Standard | Shield Advanced | WAF |
|---|---:|---:|---:|---:|
| Public static website | Recommended | Baseline | Usually unnecessary | Recommended for security-sensitive workloads |
| Public REST API | Recommended | Baseline | Evaluate based on risk | Strongly recommended |
| High-volume public API | Recommended | Baseline | Strong candidate | Strongly recommended |
| Business-critical SaaS | Recommended | Baseline | Evaluate / often justified | Strongly recommended |
| Internal-only service | Usually unnecessary | Depends on exposure | Usually unnecessary | Depends on exposure |
| Private S3 content | Recommended | Baseline | Risk-dependent | Optional / workload-dependent |
| Financially critical internet service | Recommended | Baseline | Strong candidate | Strongly recommended |
| Large public event / launch | Recommended | Baseline | Consider | Strongly recommended |

## Practical Security Baseline

For a typical production internet-facing API:

```text
                    Internet
                       │
                       ▼
               ┌───────────────┐
               │ AWS Shield     │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ CloudFront     │
               │ TLS + Cache    │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ AWS WAF        │
               │ Rules + Rate   │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ ALB            │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ Django/FastAPI │
               └───────┬───────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Redis              PostgreSQL
```

The architecture should be adapted to the application's actual requirements rather than implemented mechanically.

## Production Checklist

### Edge Protection

- [ ] CloudFront is used for appropriate internet-facing workloads.
- [ ] Shield baseline protection is understood.
- [ ] Shield Advanced requirements have been evaluated.
- [ ] CloudFront caching is configured intentionally.
- [ ] Origin Shield is evaluated for high-scale workloads where appropriate.

### WAF

- [ ] WAF is associated with the appropriate CloudFront distribution.
- [ ] Managed rules are evaluated.
- [ ] Rate-based rules protect expensive endpoints.
- [ ] Rules are tested before broad enforcement.
- [ ] WAF metrics and logs are monitored.

### Origin

- [ ] Direct origin access is restricted where practical.
- [ ] Origin transport security is configured.
- [ ] Application capacity is bounded.
- [ ] Database connections are bounded.
- [ ] Redis capacity is monitored.
- [ ] Internal retries are bounded.

### Application

- [ ] Expensive endpoints are identified.
- [ ] Authentication is required where appropriate.
- [ ] Authorization is enforced.
- [ ] Request sizes are bounded.
- [ ] Pagination limits are enforced.
- [ ] Rate limiting or quotas exist where required.
- [ ] Celery task creation is bounded.
- [ ] Timeouts and circuit breakers are configured where appropriate.

### Observability

- [ ] CloudFront metrics are monitored.
- [ ] WAF metrics are monitored.
- [ ] Origin metrics are monitored.
- [ ] Application latency and error rates are monitored.
- [ ] Database and Redis utilization are monitored.
- [ ] Attack-related alerts are defined.
- [ ] Logs can be correlated across the edge and origin.

### Incident Response

- [ ] DDoS response procedures exist.
- [ ] Ownership is defined.
- [ ] AWS escalation paths are documented.
- [ ] Emergency WAF changes are tested.
- [ ] Traffic validation procedures exist.
- [ ] Post-incident review is part of the operational process.

## Interview Traps

### Does CloudFront Replace AWS Shield?

No. CloudFront and Shield have different responsibilities. CloudFront is an edge delivery service, while Shield provides managed DDoS protection.

### Does Shield Replace AWS WAF?

No. Shield primarily addresses DDoS protection, while WAF provides application-layer HTTP request inspection and filtering.

### Is WAF Enough to Stop Every DDoS Attack?

No. WAF is primarily an HTTP/application-layer control. It is not a replacement for infrastructure-level DDoS protection.

### Does Caching Eliminate DDoS Risk?

No. Caching can reduce origin load for cacheable requests, but attackers can target dynamic or uncached resources.

### Why Should the Origin Be Protected?

If attackers can directly access the origin, they may bypass CloudFront and WAF controls and send traffic directly to the backend.

### Is Autoscaling a DDoS Mitigation Strategy?

Not by itself. Autoscaling can increase capacity but may also increase cost and downstream resource pressure. DDoS traffic should be filtered or absorbed as early as possible.

### Can Application Rate Limiting Protect Against Volumetric DDoS?

Application rate limiting is useful for application abuse, but large attacks should be mitigated closer to the network and edge rather than relying on application workers to process every request.

### Does Shield Protect Against SQL Injection?

No. SQL injection is an application-layer security problem. WAF and secure application/database design address this class of threat.

### Does Shield Protect Against Credential Stuffing?

Shield is not the primary control for credential stuffing. Authentication controls, WAF protections, rate limiting, bot controls, MFA, account protections, and application security are more relevant.

## Key Takeaways

- **Shield, CloudFront, and WAF provide complementary layers: Shield addresses DDoS protection, CloudFront provides edge delivery and caching, and WAF controls HTTP/application-layer traffic.**
- **Protect the origin from direct access so attackers cannot bypass the CloudFront security architecture.**
- **Application-layer attacks require additional controls such as rate limiting, authentication, quotas, caching, bounded resources, and protection for expensive endpoints.**
- **DDoS resilience is an architectural property: reduce traffic reaching expensive resources, prevent internal amplification, and monitor the entire request path from edge to database.**
- **Shield Advanced should be evaluated based on business risk, availability requirements, operational response needs, and DDoS-related cost exposure rather than simply treating it as a mandatory upgrade.**