# 07- Availability and Reliability

## Overview

CloudFront improves application availability by distributing content across a globally distributed edge network and reducing dependency on the origin for cacheable requests.

For a production backend, CloudFront should be treated as one layer in a larger reliability architecture:

```text
                        ┌─────────────────────┐
                        │       Viewers       │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │     CloudFront      │
                        │  Edge Distribution  │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
               Cache HIT                    Cache MISS
                    │                             │
                    ▼                             ▼
                Response                 ┌─────────────────┐
                                         │ WAF / Origin    │
                                         └────────┬────────┘
                                                  │
                                          ┌───────┴───────┐
                                          │               │
                                       Primary         Failover
                                       Origin           Origin
```

The reliability objective is not simply:

> "Keep CloudFront available."

The objective is:

> "Continue serving acceptable responses when viewers, edge locations, networks, applications, origins, dependencies, or deployments experience failures."

CloudFront can absorb substantial origin failure impact for cacheable content, but it cannot make an unhealthy dynamic backend inherently reliable.

---

## Availability vs Reliability

These terms are related but should not be treated as interchangeable.

| Concept | Meaning | CloudFront relevance |
|---|---|---|
| Availability | Whether the service can respond when requested | Edge delivery and origin availability |
| Reliability | Whether the system consistently behaves correctly | Correct caching, routing, failover, deployments |
| Durability | Whether data remains intact | Primarily origin/storage concern |
| Resilience | Ability to continue operating during failures | Caching, failover, multi-origin design |
| Recovery | Ability to restore service after failure | Origin recovery and disaster recovery |

A CloudFront distribution can remain operational while an origin is completely unavailable.

For example:

```text
CloudFront = healthy
Origin = unavailable

Cached object → can potentially continue serving
Uncached API → cannot be served successfully
```

This distinction is fundamental when designing production systems.

---

## CloudFront's Role in Availability

CloudFront improves availability through several mechanisms:

- Distributed edge delivery.
- Local serving of cached objects.
- Reduced origin dependency for cache hits.
- Origin failover for supported request patterns.
- Integration with AWS WAF.
- TLS termination at the edge.
- Connection management between edge and origin.
- Geographic distribution of traffic.

The most important mechanism for reliability is caching.

A cache hit can bypass:

```text
Load Balancer
→ Application
→ Redis
→ Database
→ External services
```

That means a healthy cached response may remain available even when downstream application components are degraded.

---

## Cache Hits as a Reliability Mechanism

Caching is normally introduced for performance, but it also creates an availability boundary.

Consider:

```mermaid
sequenceDiagram
    participant User
    participant CF as CloudFront
    participant Origin
    participant DB as PostgreSQL

    User->>CF: GET /catalog
    CF->>CF: Cache lookup

    alt Cache HIT
        CF-->>User: Cached response
    else Cache MISS
        CF->>Origin: Request
        Origin->>DB: Query
        DB-->>Origin: Data
        Origin-->>CF: Response
        CF->>CF: Store object
        CF-->>User: Response
    end
```

On subsequent requests, the database is not required for that cached object.

This creates a form of failure isolation:

```text
Viewer
  ↓
CloudFront
  ↓
Cached Object
```

instead of:

```text
Viewer
  ↓
CloudFront
  ↓
ALB
  ↓
Django/FastAPI
  ↓
Redis
  ↓
PostgreSQL
```

The shorter dependency chain is generally more resilient.

---

## What CloudFront Cannot Protect

CloudFront cannot automatically solve:

- Database failures.
- Application bugs.
- Incorrect authorization.
- Data corruption.
- Broken deployments.
- Cache poisoning.
- Incorrect cache policies.
- Origin configuration failures.
- Dependency failures for uncached requests.
- Stateful application failures.

For example:

```text
GET /api/account
```

may depend on:

```text
Authentication
Authorization
Application
Database
```

If the request must be evaluated dynamically for the authenticated user, CloudFront cannot simply serve a shared cached response.

The backend still requires its own reliability architecture.

---

## Origin Redundancy

For critical workloads, use multiple origins where the application's availability requirements justify the additional complexity.

A conceptual architecture is:

```mermaid
flowchart TD
    Viewer[Viewer] --> CF[CloudFront]

    CF --> Primary[Primary Origin]
    CF --> Secondary[Secondary Origin]

    Primary --> ALB1[ALB]
    Secondary --> ALB2[ALB]

    ALB1 --> App1[Django / FastAPI]
    ALB2 --> App2[Django / FastAPI]
```

The secondary origin can provide resilience against:

- Origin infrastructure failure.
- Regional problems.
- Application deployment failures.
- Network connectivity issues.
- Operational incidents.

The failover architecture must be tested rather than assumed to work.

---

## Origin Failover

CloudFront supports origin groups for failover scenarios.

The basic model is:

```text
Viewer
  ↓
CloudFront
  ↓
Primary Origin
  │
  ├── Success → Response
  │
  └── Failover condition
          ↓
      Secondary Origin
          ↓
       Response
```

Failover is generally driven by configured HTTP status codes or origin failures associated with the cache behavior.

A production design should carefully choose which failures should trigger failover.

---

## Failover Status Codes

Not every error should cause an origin failover.

For example:

```text
500 Internal Server Error
503 Service Unavailable
504 Gateway Timeout
```

may indicate an origin failure.

But:

```text
401 Unauthorized
403 Forbidden
404 Not Found
```

often represent legitimate application responses.

Failing over a `404` to another origin may be incorrect if the resource genuinely does not exist.

A useful rule is:

> Fail over infrastructure failures, not ordinary business responses.

The exact failover policy should match the application's semantics.

---

## Primary and Secondary Origin Design

A secondary origin can be:

- Another ALB.
- Another regional deployment.
- Another S3 bucket.
- Another service endpoint.
- Another application environment designed for disaster recovery.

The secondary origin must actually be capable of serving the required workload.

A common mistake is:

```text
Primary production system
+
Unmaintained secondary origin
```

This provides theoretical redundancy but weak operational reliability.

Secondary infrastructure should have:

- Tested deployments.
- Compatible application versions.
- Required configuration.
- Required secrets.
- Database connectivity.
- Monitoring.
- Capacity.
- Security controls.

---

## Active-Active vs Active-Passive

Two common architectures are:

| Architecture | Description | Advantages | Limitations |
|---|---|---|---|
| Active-active | Multiple origins serve traffic normally | High availability, better utilization | More complexity |
| Active-passive | Secondary primarily waits for failover | Simpler traffic model | Capacity and drift risks |

Active-active systems require stronger consistency and routing design.

Active-passive systems require confidence that the standby environment can actually become production-ready quickly.

---

## Multi-Region Reliability

A multi-region architecture can reduce the blast radius of regional failures.

Example:

```mermaid
flowchart LR
    User[Global Users] --> CF[CloudFront]

    CF --> US[Region A]
    CF --> EU[Region B]

    US --> AppA[Application]
    EU --> AppB[Application]

    AppA --> DBA[(Database)]
    AppB --> DBB[(Database)]
```

The difficult part is usually not CloudFront.

The difficult part is maintaining:

- Application consistency.
- Database replication.
- Configuration consistency.
- Secrets.
- Background jobs.
- Object storage.
- Session handling.
- Observability.
- Deployment compatibility.

Multi-region should therefore be justified by the required availability and recovery objectives.

---

## RTO and RPO

CloudFront reliability planning should be aligned with application recovery objectives.

### Recovery Time Objective

RTO answers:

> How long can the service be unavailable before recovery is unacceptable?

### Recovery Point Objective

RPO answers:

> How much data loss can the business tolerate?

For example:

```text
RTO = 15 minutes
RPO = 5 minutes
```

CloudFront can help with availability for cached content, but RTO and RPO for dynamic applications depend heavily on:

- Application recovery.
- Database replication.
- Infrastructure automation.
- Data restoration.
- DNS/routing.
- Deployment pipelines.

---

## Health Checks

Health checking determines whether an origin is capable of serving traffic.

A good health endpoint should be lightweight and deterministic.

For example:

```http
GET /healthz
```

A simple application response might be:

```json
{
  "status": "ok"
}
```

Do not make health checks unnecessarily expensive.

Avoid:

```text
/healthz
    ↓
PostgreSQL query
    ↓
Redis query
    ↓
External API call
```

unless the purpose is explicitly to verify dependency readiness.

For basic liveness, a lightweight endpoint is preferable.

---

## Liveness vs Readiness

These concepts are especially important when CloudFront sits in front of Kubernetes, Django, or FastAPI services.

| Check | Question |
|---|---|
| Liveness | Is the process alive? |
| Readiness | Can this instance serve production traffic? |
| Dependency health | Are required dependencies operational? |

A Kubernetes pod can be alive but not ready.

Similarly, an origin can respond to TCP connections but still be incapable of serving meaningful application traffic.

Reliability decisions should use the appropriate health signal.

---

## Origin Timeout Design

Timeouts are reliability controls, not just performance settings.

Suppose:

```text
CloudFront
    ↓
ALB
    ↓
Django
    ↓
PostgreSQL
```

If the database becomes slow, requests can accumulate.

Eventually:

```text
Requests waiting
    ↓
Application workers exhausted
    ↓
ALB queues increase
    ↓
CloudFront waits
    ↓
Timeouts increase
    ↓
Retry traffic increases
```

This can become a cascading failure.

Timeouts should therefore be bounded across the request chain.

---

## Cascading Failure

A classic failure pattern is:

```mermaid
flowchart TD
    DB[Slow Database] --> App[Application Threads / Workers]
    App --> ALB[Load Balancer]
    ALB --> CF[CloudFront]
    CF --> Retry[Client Retries]
    Retry --> CF
    CF --> ALB
    ALB --> App
```

The system can become overloaded because every layer waits for the previous layer.

Mitigations include:

- Appropriate timeouts.
- Connection limits.
- Circuit breakers.
- Backpressure.
- Rate limiting.
- Caching.
- Queue-based asynchronous processing.
- Database optimization.
- Controlled retries.

---

## Retry Storms

CloudFront is not the only source of repeated traffic.

Clients, SDKs, mobile applications, reverse proxies, and backend services may retry failed requests.

A failure can therefore produce:

```text
Failure
  ↓
Retry
  ↓
More load
  ↓
More failures
  ↓
More retries
```

Use retries carefully.

For dynamic APIs, clients should generally use:

- Exponential backoff.
- Jitter.
- Retry limits.
- Idempotent operations.

Never blindly retry every HTTP method or every status code.

---

## Static Content Reliability

Static content is one of the strongest CloudFront reliability use cases.

For assets such as:

```text
JavaScript
CSS
Images
Fonts
Downloads
Public documentation
```

use:

- Long TTLs.
- Content-hashed filenames.
- Versioned deployments.
- Durable origin storage.
- Appropriate cache policies.

Example:

```text
app.91a73f.js
app.b82d11.js
```

Old versions can remain available while new versions propagate.

This reduces deployment-time dependency on cache invalidation.

---

## Dynamic API Reliability

Dynamic APIs require more careful design.

Example:

```text
CloudFront
    ↓
ALB
    ↓
Django / FastAPI
    ↓
Redis
    ↓
PostgreSQL
```

Reliability should be addressed at every layer:

| Layer | Reliability mechanism |
|---|---|
| CloudFront | Distributed edge delivery |
| WAF | Controlled traffic filtering |
| ALB | Multi-AZ load balancing |
| Application | Multiple instances |
| Redis | Appropriate replication/failover strategy |
| PostgreSQL | Backups, replication, failover |
| Kubernetes | Multiple replicas and nodes |
| Background jobs | Durable queue and retry strategy |

CloudFront should not become an excuse to ignore backend reliability.

---

## Availability Zones

When the origin runs on AWS compute infrastructure, deploy it across multiple Availability Zones where the workload requires high availability.

Example:

```text
                CloudFront
                    │
                   ALB
             ┌──────┴──────┐
             │             │
           AZ-A           AZ-B
             │             │
          App-1          App-2
             │             │
             └──────┬──────┘
                    │
               Database
```

A single EC2 instance or single-AZ application behind CloudFront remains a single point of failure.

CloudFront provides global edge distribution; it does not eliminate origin single points of failure.

---

## Kubernetes Reliability

For Kubernetes-hosted applications:

```text
CloudFront
    ↓
ALB / Ingress
    ↓
Service
    ↓
Pods
```

Use appropriate:

- Replica counts.
- Pod disruption budgets.
- Readiness probes.
- Liveness probes.
- Horizontal Pod Autoscaling.
- Node distribution.
- Rolling deployments.

Avoid deploying all replicas onto one failure domain.

---

## Deployment Reliability

A large percentage of production incidents are deployment-related rather than infrastructure-related.

CloudFront deployments should use:

- Immutable assets.
- Backward-compatible API changes.
- Automated validation.
- Canary or staged deployments where justified.
- Rollback procedures.
- Cache behavior awareness.

A problematic deployment can be amplified by caching.

For example:

```text
Bad response cached
    ↓
Many viewers receive bad response
```

The cache can therefore increase the blast radius of an incorrect response.

---

## Cache Poisoning and Reliability

Incorrect cache configuration can create reliability failures.

For example:

```text
Request A
→ Response cached incorrectly

Request B
→ Receives cached response from A
```

The problem may involve:

- Missing cache-key dimensions.
- Incorrect query-string handling.
- Incorrect cookie handling.
- Incorrect headers.
- Personalized responses being cached.

Caching must preserve response correctness, not merely improve hit ratio.

---

## Stale Content Tradeoffs

Long TTLs improve cache efficiency but increase the time incorrect content may remain available.

The tradeoff is:

```text
Long TTL
    ↓
Higher cache reuse
    ↓
Lower origin dependency
    ↓
Potentially longer stale window
```

For immutable assets, this is usually desirable.

For frequently changing business data, it may not be.

TTL should be selected based on the application's consistency requirements.

---

## Graceful Degradation

A reliable system does not always need to return the complete ideal response.

For example, a product page may continue displaying:

```text
Cached product information
```

while temporarily omitting:

```text
Recommendations
```

if the recommendation service is unavailable.

A backend architecture should distinguish:

```text
Critical dependency
vs
Optional dependency
```

CloudFront can provide resilience for cacheable components, while the application handles graceful degradation for dynamic dependencies.

---

## Error Responses

Error handling should be deliberate.

CloudFront can be configured to provide custom error responses for appropriate use cases.

For example:

```text
404
→ branded application error page
```

or:

```text
503
→ temporary service-unavailable response
```

Do not cache errors indiscriminately.

An origin outage should not result in a long-lived cached error if the application should recover quickly.

Error caching TTL should be aligned with recovery expectations.

---

## Monitoring Availability

Monitor both CloudFront and origin health.

Important signals include:

| Metric / Signal | Reliability question |
|---|---|
| 4xx error rate | Are clients generating invalid requests? |
| 5xx error rate | Is the system failing? |
| Origin latency | Is the backend becoming slow? |
| Origin requests | Is cache efficiency degrading? |
| Cache hit ratio | Is the origin being unnecessarily exposed? |
| Requests | Is traffic abnormal? |
| Bytes downloaded | Is traffic volume changing? |
| Origin health | Can the backend serve requests? |

A CloudFront `5xx` increase should be correlated with origin metrics rather than investigated in isolation.

---

## Availability SLOs

Define SLOs at the user-facing level.

For example:

```text
99.9% of valid API requests
must complete successfully
within the defined latency target.
```

Then map the SLO across layers:

```text
Viewer
  ↓
CloudFront
  ↓
WAF
  ↓
ALB
  ↓
Application
  ↓
Database
```

If CloudFront is healthy but PostgreSQL is unavailable, the user-facing SLO can still fail.

The SLO should therefore measure the actual service outcome.

---

## Failure Detection Workflow

When users report an outage:

```mermaid
flowchart TD
    A[User reports failure] --> B[Check CloudFront 4xx/5xx]
    B --> C{CloudFront errors elevated?}

    C -->|No| D[Inspect client/application behavior]
    C -->|Yes| E[Check origin requests and latency]

    E --> F{Origin unhealthy?}
    F -->|Yes| G[Investigate ALB / App / DB]
    F -->|No| H[Inspect CloudFront configuration]

    G --> I[Recover origin]
    H --> J[Inspect cache / WAF / TLS / routing]

    I --> K[Validate recovery]
    J --> K
```

Avoid immediately changing configuration during an incident without identifying the failing layer.

---

## Disaster Recovery

CloudFront should be part of the disaster recovery design rather than the entire DR strategy.

A mature architecture considers:

```text
Application
+
Database
+
Object Storage
+
Secrets
+
Infrastructure
+
CloudFront
+
DNS
+
Monitoring
```

Recovery automation should be tested regularly.

Useful DR practices include:

- Infrastructure as code.
- Version-controlled CloudFront configuration.
- Automated origin provisioning.
- Database backups.
- Cross-region replication where required.
- Tested failover.
- Documented rollback procedures.
- Periodic disaster recovery exercises.

---

## Infrastructure as Code

CloudFront configuration should be reproducible.

Example Terraform structure:

```hcl
resource "aws_cloudfront_distribution" "application" {
  enabled = true

  origin {
    domain_name = aws_lb.application.dns_name
    origin_id   = "application-origin"
  }

  default_cache_behavior {
    target_origin_id       = "application-origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS"
    ]

    cached_methods = [
      "GET",
      "HEAD"
    ]
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

Production configurations should normally use explicit ACM certificates, security policies, cache policies, origin request policies, and WAF associations appropriate to the workload.

The important reliability principle is that the configuration must be recoverable without manually reconstructing it during an outage.

---

## Configuration Drift

Manual console changes can create drift between:

```text
Git repository
vs
AWS environment
```

This becomes dangerous during disaster recovery.

For example:

```text
Production distribution
→ manually modified

Terraform
→ old configuration
```

A future deployment may unintentionally revert the production fix.

Prefer:

```text
Git
  ↓
CI/CD
  ↓
Infrastructure as Code
  ↓
CloudFront
```

Emergency changes should be reconciled back into source control.

---

## Security and Reliability

Security failures can become availability failures.

Examples include:

- WAF rules blocking legitimate traffic.
- Incorrect geo restrictions.
- Broken signed URLs.
- Incorrect origin access controls.
- TLS configuration errors.
- Authentication headers being mishandled.
- Rate limits blocking legitimate clients.

Security configuration should therefore be tested against production traffic patterns.

---

## Cost and Reliability Tradeoffs

Higher availability often costs more.

Examples:

```text
Single origin
→ cheaper
→ larger failure domain

Multiple origins
→ more expensive
→ better resilience

Single region
→ simpler
→ regional failure risk

Multi-region
→ more expensive
→ reduced regional blast radius
```

Do not design for maximum theoretical availability without considering business requirements.

The architecture should meet the required:

```text
SLO
RTO
RPO
```

at an economically justified cost.

---

## Common Reliability Mistakes

### Treating CloudFront as a Complete HA Solution

CloudFront cannot make a single unhealthy origin highly available.

### Using One Origin Instance

A single EC2 instance remains a single point of failure.

### No Origin Failover Strategy

Critical applications may require a secondary origin or another recovery mechanism.

### Failing Over on Every Error

Business errors such as `404` or `403` should not automatically trigger infrastructure failover.

### Overly Long Error Caching

A temporary origin failure can become a prolonged user-facing failure if the error response is cached too aggressively.

### Caching Personalized Responses

This can cause both security and correctness failures.

### Ignoring Cache Miss Capacity

The origin must handle more than the average cache-miss rate.

### Untested Disaster Recovery

A documented failover procedure that has never been tested should not be considered reliable.

### Health Checks That Are Too Expensive

A health endpoint that queries every dependency can itself contribute to an outage.

### No Deployment Rollback

CloudFront configuration and application deployments should have explicit rollback procedures.

---

## Production Reliability Checklist

### CloudFront

- [ ] CloudFront is deployed for appropriate workloads
- [ ] Cache policies are explicitly designed
- [ ] Cache keys do not create unnecessary fragmentation
- [ ] Personalized responses are protected from shared caching
- [ ] Error caching behavior is intentional
- [ ] TLS configuration is production-ready

### Origin

- [ ] Origin runs across appropriate Availability Zones
- [ ] Application instances are redundant
- [ ] Origin capacity handles cache misses
- [ ] Health checks are configured
- [ ] Origin timeouts are bounded
- [ ] Failure behavior is documented

### Failover

- [ ] Secondary origin exists when required
- [ ] Failover status codes are intentional
- [ ] Secondary origin has sufficient capacity
- [ ] Failover configuration is managed as code
- [ ] Failover has been tested

### Application

- [ ] Django/FastAPI instances are redundant
- [ ] Database failure behavior is understood
- [ ] Redis failure behavior is understood
- [ ] External dependency failures are handled
- [ ] Retries use backoff and jitter
- [ ] Critical and optional dependencies are distinguished

### Kubernetes

- [ ] Pods are distributed across failure domains
- [ ] Readiness probes are configured
- [ ] Liveness probes are appropriate
- [ ] HPA behavior is validated
- [ ] Rolling deployments are safe
- [ ] Pod disruption behavior is understood

### Observability

- [ ] CloudFront 4xx and 5xx rates are monitored
- [ ] Origin latency is monitored
- [ ] Cache hit ratio is monitored
- [ ] Origin request volume is monitored
- [ ] Alerts are tied to user-facing SLOs
- [ ] Logs are sufficient for incident investigation

### Disaster Recovery

- [ ] RTO is defined
- [ ] RPO is defined
- [ ] CloudFront configuration is reproducible
- [ ] Origin infrastructure is reproducible
- [ ] Database recovery is tested
- [ ] Failover procedures are documented
- [ ] Disaster recovery exercises are performed

---

## Interview Traps

### Does CloudFront make an application highly available?

Not by itself.

It improves availability for content that can be served from the edge, but dynamic requests can still depend entirely on the origin.

### Why does caching improve reliability?

A cache hit removes downstream dependencies from the request path, reducing the number of components that must be healthy for the response to succeed.

### Should every 5xx trigger origin failover?

Not blindly.

The failover policy should distinguish infrastructure failures from application-level behavior and should be tested against the application's error semantics.

### Is multi-region always better?

No.

Multi-region improves resilience against certain failure domains but introduces substantial complexity in data, deployments, operations, observability, and consistency.

### Why can CloudFront increase the impact of a bad deployment?

A bad response can be cached and subsequently served to many viewers. Cache policy, TTL, deployment strategy, and invalidation procedures must therefore be considered together.

### Does a healthy CloudFront distribution mean the application is healthy?

No.

CloudFront can be healthy while the origin, database, or application is failing.

## Key Takeaways

- **CloudFront improves availability primarily by reducing origin dependency:** cache hits can continue serving content without requiring the application, Redis, or database to be healthy.
- **CloudFront is not a substitute for origin high availability:** production systems still require redundant application infrastructure, appropriate database resilience, and tested recovery mechanisms.
- **Design failover around failure semantics:** fail over infrastructure failures deliberately rather than treating every HTTP error as an origin failure.
- **Reliability requires capacity, observability, and testing:** monitor CloudFront and origin behavior together, size for cache misses and spikes, and regularly test failover and disaster recovery.
- **Design against explicit SLO, RTO, and RPO requirements:** multi-region and multi-origin architectures should be justified by business recovery requirements rather than theoretical maximum availability.