# 04- Origin Groups and Failover

## Overview

CloudFront origin groups provide a controlled failover mechanism between a **primary origin** and one or more **secondary origins**. They are used when a request should normally be served by one origin but should have an alternative origin available when the primary cannot successfully serve the request.

This is different from ordinary multi-origin routing.

```text
Multi-Origin Routing

/static/* ──► S3
/api/*    ──► ALB
/media/*  ──► S3
```

Here, different request patterns intentionally use different origins.

Origin failover instead looks like:

```text
/api/*
   │
   ▼
Primary Origin
   │
   ├── Success ───────► Client
   │
   └── Failure
          │
          ▼
    Secondary Origin
          │
          ▼
        Client
```

Origin groups are useful for improving availability when the secondary origin is genuinely capable of serving the same request correctly. They should not be treated as a generic load-balancing mechanism or as a complete disaster-recovery solution.

A senior-level design question is therefore not simply:

> "Can I configure a secondary origin?"

It is:

> "Can the secondary origin independently and correctly serve the request when the primary origin fails?"

That distinction determines whether origin failover provides meaningful resilience or merely adds configuration complexity.

## Multi-Origin Routing vs Origin Failover

These concepts are related but solve different problems.

| Capability | Purpose |
|---|---|
| Multiple origins | Support different workloads |
| Cache behaviors | Select an origin based on request path/behavior |
| Origin group | Fail over from a primary origin to a secondary origin |
| Origin failover | Continue serving a request when the primary origin returns configured failure responses |
| Multi-region architecture | Provide geographic and regional resilience |
| Load balancer | Distribute traffic across healthy backend targets |

For example:

```text
CloudFront
│
├── /static/* ──► S3
│
└── /api/* ─────► ALB
```

is multi-origin routing.

Whereas:

```text
CloudFront
│
└── /api/*
       │
       ▼
   Origin Group
       │
       ├── Primary ───► ALB Region A
       │
       └── Secondary ─► ALB Region B
```

is origin failover.

## Why Origin Groups Exist

A single origin creates a dependency:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin
```

If the origin becomes unavailable, requests that require that origin may fail.

An origin group introduces an alternative:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Primary Origin
  │
  └── failure
       │
       ▼
Secondary Origin
```

The goal is to reduce the impact of an origin failure without requiring the client to know that a second backend exists.

This can be valuable for:

- Regional application deployments.
- Backup content stores.
- Static content redundancy.
- Disaster-recovery paths.
- Legacy-to-new backend transitions.
- Read-only fallback systems.

## Origin Group Architecture

A simplified architecture looks like this:

```mermaid
flowchart TD
    Client[Client] --> CF[CloudFront Distribution]
    CF --> Behavior[Cache Behavior]
    Behavior --> Group[Origin Group]

    Group --> Primary[Primary Origin]
    Group --> Secondary[Secondary Origin]

    Primary --> PrimaryApp[Primary Backend]
    Secondary --> SecondaryApp[Secondary Backend]
```

The important control flow is:

```text
Viewer Request
      ↓
Cache Behavior
      ↓
Origin Group
      ↓
Primary Origin
      ↓
Failure?
      ↓
Secondary Origin
```

CloudFront remains the public edge endpoint. The viewer does not need to perform a second request against the secondary origin.

## Primary and Secondary Origins

An origin group normally has a primary origin and a secondary origin.

### Primary Origin

The primary origin is the normal source of content.

Examples:

```text
Primary:
ALB in us-east-1
```

or:

```text
Primary:
S3 bucket containing production assets
```

The primary origin should be considered the normal production path.

### Secondary Origin

The secondary origin is the fallback source.

Examples:

```text
Secondary:
ALB in eu-west-1
```

or:

```text
Secondary:
S3 backup bucket
```

The secondary must be able to provide a valid response for the requests that can fail over to it.

A secondary origin that contains stale, incomplete, or incompatible data is not a valid high-availability fallback merely because it is reachable.

## Failover Criteria

CloudFront determines whether an origin request should fail over based on configured origin-group failover criteria.

Common failure responses used for failover include HTTP error statuses such as:

- `400`
- `403`
- `404`
- `500`
- `502`
- `503`
- `504`

The exact configuration should be selected according to the application semantics.

For example:

```text
Primary returns 503
       │
       ▼
Configured as failover status
       │
       ▼
CloudFront attempts secondary
```

The important distinction is that failover is not triggered simply because the application "looks unhealthy" from an architectural perspective.

The configured HTTP response behavior matters.

## Why Failover Status Selection Matters

Choosing failover status codes requires care.

Suppose the primary application returns:

```http
404 Not Found
```

because the requested resource genuinely does not exist.

If `404` is configured as a failover condition:

```text
Client
  │
  ▼
Primary
  │
  └── 404
       │
       ▼
Secondary
```

CloudFront may send the request to the secondary even though the primary was functioning correctly.

This can create unnecessary origin traffic and potentially inconsistent behavior.

Therefore, failover status codes should represent conditions where the secondary origin has a meaningful chance of satisfying the request.

## Request Lifecycle

A typical failover request follows this flow:

```mermaid
sequenceDiagram
    participant Client
    participant CF as CloudFront
    participant Primary
    participant Secondary

    Client->>CF: GET /api/orders/123
    CF->>CF: Match cache behavior
    CF->>Primary: Forward request

    alt Primary succeeds
        Primary-->>CF: 200 OK
        CF-->>Client: 200 OK
    else Primary returns failover status
        Primary-->>CF: 503 Service Unavailable
        CF->>Secondary: Forward request
        Secondary-->>CF: 200 OK
        CF-->>Client: 200 OK
    end
```

The critical point is that failover occurs as part of the CloudFront-to-origin request path.

The client generally does not need to know that the first origin failed.

## Origin Groups and Cache Behaviors

An origin group is associated with CloudFront behavior configuration.

For example:

| Path Pattern | Origin |
|---|---|
| `/static/*` | S3 |
| `/api/*` | API Origin Group |
| `/media/*` | S3 |

The API behavior can reference an origin group:

```text
/api/*
    │
    ▼
API Origin Group
    │
    ├── Primary API
    └── Secondary API
```

This allows failover to be scoped to a particular workload.

It is usually preferable to fail over only the traffic that has a valid fallback rather than treating every CloudFront request as part of one large failover domain.

## Static Content Failover

Static content is often one of the simplest origin-group use cases.

```text
CloudFront
    │
    ▼
Static Origin Group
    │
    ├── Primary S3
    │
    └── Secondary S3
```

For example:

```text
Primary:
s3://production-assets-primary

Secondary:
s3://production-assets-secondary
```

The secondary bucket should contain the content required to serve the expected request paths.

A useful property of static failover is that the application does not need to execute when the fallback object already exists.

## Application Failover

Application failover is more difficult.

Consider:

```text
CloudFront
    │
    ▼
Origin Group
    │
    ├── Region A ALB
    │       │
    │       ▼
    │   Django/FastAPI
    │
    └── Region B ALB
            │
            ▼
        Django/FastAPI
```

The secondary application must be capable of serving the same external API contract.

That includes:

- Routes.
- Authentication.
- Authorization.
- Response schemas.
- Required configuration.
- Database access.
- Storage access.
- Secrets.
- External dependencies.

If Region B has a different application version, failover may produce inconsistent responses.

## Stateless Application Failover

Stateless applications are significantly easier to fail over.

For example:

```text
Region A
├── Django
└── PostgreSQL

Region B
├── Django
└── PostgreSQL
```

If Django instances do not maintain local session state, the application layer can be replicated more easily.

However, the database remains a critical dependency.

A common mistake is:

```text
Two application regions
        │
        ▼
One PostgreSQL database
```

and then assuming the architecture is fully multi-region.

The application layer may be redundant while the database remains a single failure domain.

## Database Dependency

Application failover is only meaningful if the secondary application can access the required data.

Consider:

```text
CloudFront
    │
    ├── Primary App ──► Primary DB
    │
    └── Secondary App ──► Primary DB
```

If the primary region fails and the database is also unavailable:

```text
Secondary App
      │
      ▼
Unavailable DB
```

then CloudFront failover does not restore application availability.

A more resilient design might involve:

```text
Primary App ──► Primary Database
                     │
                     │ replication
                     ▼
Secondary App ──► Secondary Database
```

The exact database topology depends on the consistency, write, and recovery requirements.

## Read-Only Failover

One practical pattern is to make the secondary origin read-only.

For example:

```text
Primary Origin
    │
    ├── GET
    ├── POST
    ├── PUT
    └── DELETE

Secondary Origin
    │
    └── GET only
```

This can be useful for:

- Product catalogs.
- Documentation.
- Public content.
- Status pages.
- Read-only APIs.

However, it is not appropriate for an API where users must continue performing writes during an outage.

Failover design must therefore match the business operation being protected.

## Failover and HTTP Methods

An important design consideration is the request method.

Consider:

```http
POST /orders
```

If the primary origin partially processes the request and then returns an error, automatically attempting the same operation against the secondary can create duplicate side effects.

For example:

```text
Client
  │
  │ POST /orders
  ▼
Primary
  │
  ├── Creates order
  │
  └── Returns 503
        │
        ▼
CloudFront
        │
        ▼
Secondary
        │
        └── Creates another order
```

This is a serious distributed-systems problem.

Therefore, automatic origin failover is much easier to reason about for:

- `GET`
- `HEAD`
- Other idempotent/read-oriented requests

than for non-idempotent operations.

For state-changing APIs, use strong idempotency guarantees and carefully validate whether failover is appropriate.

## Idempotency

If a write operation can be retried, the application should support an idempotency mechanism.

For example:

```http
POST /payments
Idempotency-Key: 9d4c7f...
```

The backend can persist the idempotency key:

```text
Idempotency Key
       │
       ▼
Redis / PostgreSQL
       │
       ▼
Previously processed?
   ┌───┴───┐
   │       │
  Yes      No
   │       │
Return    Process
existing    │
response    ▼
          Store result
```

This does not make CloudFront failover inherently safe, but it can reduce duplicate side effects when requests are retried across failure boundaries.

## Origin Groups Are Not Load Balancers

An origin group should not be treated as:

```text
Primary
   │
   ├── 50%
   └── 50%
Secondary
```

Origin groups are designed around **primary/secondary failover**, not general-purpose traffic distribution.

If the requirement is:

> Send traffic across several healthy application instances.

Use an appropriate load-balancing architecture, such as:

```text
CloudFront
    │
    ▼
ALB
    │
    ├── Target A
    ├── Target B
    └── Target C
```

If the requirement is:

> Use another origin when the primary cannot serve the request.

An origin group may be appropriate.

## Origin Groups vs ALB Failover

These mechanisms operate at different layers.

| Layer | Mechanism | Responsibility |
|---|---|---|
| CloudFront | Origin group | Select fallback origin |
| ALB | Target groups | Distribute traffic among backend targets |
| Kubernetes | Service/load balancing | Route to application pods |
| Application | Retry logic | Retry downstream operations |
| Database | Replication/failover | Maintain database availability |

A production architecture can use several of these mechanisms together.

For example:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin Group
  │
  ├── Primary ALB
  │      │
  │      ├── App A
  │      └── App B
  │
  └── Secondary ALB
         │
         ├── App C
         └── App D
```

Each layer solves a different availability problem.

## Regional Failover

A common advanced architecture is:

```mermaid
flowchart TD
    Client[Client] --> CF[CloudFront]

    CF --> Group[Origin Group]

    Group --> Primary[Primary Region]
    Group --> Secondary[Secondary Region]

    Primary --> ALB1[ALB]
    ALB1 --> App1[Django / FastAPI]
    App1 --> DB1[(Primary Database)]

    Secondary --> ALB2[ALB]
    ALB2 --> App2[Django / FastAPI]
    App2 --> DB2[(Secondary Database)]

    DB1 -. Replication / DR .-> DB2
```

This can improve regional resilience, but it introduces additional engineering requirements.

You must define:

- Which region accepts writes.
- How data is replicated.
- How stale data is tolerated.
- How authentication state works.
- How background jobs are coordinated.
- How duplicate processing is prevented.
- How DNS and external integrations behave.
- How the secondary region is promoted.

CloudFront cannot solve these problems by itself.

## Failover and Data Consistency

Suppose:

```text
Primary Region:
Order #123 = PAID

Secondary Region:
Order #123 = PENDING
```

If CloudFront fails over to the secondary region, the client may observe:

```text
GET /orders/123
→ PENDING
```

even though the primary had already recorded:

```text
PAID
```

This is a data-consistency problem, not an edge-routing problem.

Senior-level architecture requires defining acceptable consistency behavior during failover.

## Origin Health and Failover

Origin failover is based on CloudFront's configured response-based failover behavior.

Do not assume that CloudFront will continuously understand every internal application dependency.

For example:

```text
Application
    │
    ├── PostgreSQL ❌
    │
    └── Redis ❌
```

may result in:

```http
HTTP/1.1 503 Service Unavailable
```

If `503` is configured as a failover response, CloudFront can attempt the secondary origin.

The application should therefore expose meaningful HTTP failure responses when appropriate.

## Health Checks vs Request-Time Failover

These are conceptually different.

### Health Checks

A health-check system periodically asks:

```text
Is the backend healthy?
```

### Request-Time Failover

CloudFront evaluates the response to an actual request:

```text
Request
   │
   ▼
Primary
   │
   ▼
Failure response
   │
   ▼
Secondary
```

A backend can pass a health check and still fail a real request.

Conversely, a health check may fail while some production requests could still succeed.

Therefore, health monitoring and request-level failover should be treated as complementary mechanisms rather than interchangeable concepts.

## Failover and Caching

Caching can affect how failures are observed.

A successful response may already exist in the CloudFront cache:

```text
Client
  │
  ▼
CloudFront
  │
  └── Cache Hit
```

In that situation, CloudFront may satisfy the request without contacting the primary or secondary origin.

This is generally beneficial for availability and latency.

However, stale cached content may hide an origin outage temporarily.

For operational analysis, distinguish:

```text
Cache availability
```

from:

```text
Origin availability
```

A CloudFront cache hit does not prove that the origin is currently healthy.

## Error Caching

CloudFront can cache error responses depending on its configuration.

This has operational consequences.

Suppose the primary origin temporarily returns:

```http
503 Service Unavailable
```

If the error response is cached, subsequent requests may continue seeing the error even after the origin recovers, depending on the configured error-caching behavior.

Therefore, when designing failover, consider:

- Which error responses trigger failover.
- How errors are cached.
- How long error responses remain cached.
- Whether failover responses can themselves be cached.
- How recovery propagates.

## Failover Recovery

A failover architecture needs a recovery strategy.

Consider:

```text
Primary
   │
   └── failure
        │
        ▼
Secondary
```

After the primary recovers, the architecture must return to:

```text
Primary
   │
   ▼
Normal traffic
```

CloudFront origin groups are not a complete application-state orchestration system.

The primary backend must be repaired and validated independently.

Operational recovery may require:

1. Detecting the failure.
2. Confirming secondary availability.
3. Repairing the primary.
4. Validating application correctness.
5. Validating data consistency.
6. Confirming the primary is safe to receive traffic.
7. Monitoring the transition back to normal operation.

## Failback Risks

Failing back to the primary can introduce another outage if the primary is only partially recovered.

For example:

```text
Primary
   │
   ├── ALB healthy
   ├── Application healthy
   └── Database synchronization incomplete
```

The infrastructure may appear healthy while the application state is not ready.

Therefore:

> Infrastructure health does not necessarily equal application readiness.

Use application-level readiness criteria when deciding whether a region or origin is truly ready for production traffic.

## Security Considerations

Both origins must be secured independently.

A common architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Origin Group
   │
   ├── Primary ALB
   └── Secondary ALB
```

If users can bypass CloudFront and access either ALB directly, the edge security model may be weakened.

Security controls should include appropriate:

- TLS.
- Authentication.
- Authorization.
- WAF controls.
- Origin access restrictions.
- Security groups.
- Application-level protections.
- Logging.

For S3 origins, use appropriate CloudFront access controls rather than making a private bucket broadly public simply to enable fallback.

## Security Consistency Between Origins

A common failover mistake is:

```text
Primary:
Authentication enabled

Secondary:
Authentication misconfigured
```

When failover occurs, the application's security posture changes.

The primary and secondary origins should therefore be equivalent from the perspective of:

- Authentication.
- Authorization.
- Rate limiting.
- Input validation.
- Security headers.
- Data access controls.

A fallback that is less secure than the primary is not an acceptable production fallback.

## Observability

Origin failover requires visibility into both origins.

At the CloudFront layer, monitor:

- Requests.
- 4xx responses.
- 5xx responses.
- Cache hit ratio.
- Origin response behavior.
- Latency.
- Error patterns.

At the origin layer, monitor:

- ALB health.
- Target health.
- Application errors.
- Database availability.
- Dependency failures.
- CPU and memory.
- Network saturation.

The important operational question is:

> Did CloudFront fail over, and why?

Without correlated logs and metrics, this can be difficult to determine.

## Logging Strategy

A useful architecture is:

```text
CloudFront Logs
      │
      ▼
Observability Platform
      │
      ├── Primary Origin Logs
      │
      └── Secondary Origin Logs
```

Correlate requests using identifiers where possible.

For APIs, propagate a request or correlation ID:

```http
X-Request-ID: 7f4d1c...
```

This makes it easier to trace:

```text
Client
 → CloudFront
 → Primary
 → Secondary
 → Application
```

during failure scenarios.

## Monitoring Metrics

A production dashboard should distinguish normal origin traffic from failover traffic.

Useful signals include:

| Metric | Why It Matters |
|---|---|
| CloudFront 5xx | Detect edge/origin failures |
| Origin latency | Detect backend degradation |
| Cache hit ratio | Understand origin load |
| Primary origin errors | Detect primary failure |
| Secondary origin traffic | Detect failover |
| ALB target health | Validate backend capacity |
| Application 5xx | Detect application failures |
| Database errors | Detect shared dependency failures |

A sudden increase in secondary-origin traffic should normally be treated as an operational event.

## Alerting

Do not alert only on total CloudFront availability.

For example:

```text
CloudFront 200 rate: 99.99%
```

may appear healthy while:

```text
Primary origin: DOWN
Secondary origin: serving 100%
```

This is a degraded state.

The system should therefore distinguish:

```text
Healthy
Degraded / Failover Active
Failed
```

rather than treating all successful viewer responses as equivalent.

## Performance Considerations

Failover introduces additional request-path complexity.

Normal path:

```text
Client
 → CloudFront
 → Primary
```

Failover path:

```text
Client
 → CloudFront
 → Primary
 → Failure
 → Secondary
```

The failed primary request adds latency before the secondary response is returned.

This means failover is a resilience mechanism, not a performance optimization.

If primary-origin failures are frequent, investigate the underlying cause rather than relying on the secondary indefinitely.

## Cost Considerations

Failover can increase cost because the secondary environment may need to remain operational.

Depending on the architecture, this can involve:

- Additional ALBs.
- Additional compute.
- Additional databases.
- Cross-region replication.
- Additional storage.
- Additional data transfer.
- Additional observability infrastructure.

A cold standby may reduce infrastructure cost but increase recovery time.

A warm or active secondary may improve recovery time but cost more.

The appropriate model depends on the required RTO and RPO.

## RTO and RPO

Origin failover should be evaluated against recovery objectives.

| Concept | Meaning |
|---|---|
| RTO | Maximum acceptable recovery time |
| RPO | Maximum acceptable data loss |

For example:

```text
RTO: 5 minutes
RPO: 1 minute
```

requires a substantially different architecture from:

```text
RTO: 24 hours
RPO: 24 hours
```

CloudFront failover can reduce part of the traffic-routing recovery time, but it does not automatically satisfy the overall RTO/RPO requirements.

## Disaster Recovery Architecture

A stronger DR architecture may look like:

```text
                    CloudFront
                        │
                        ▼
                 Origin Group
                  /          \
                 /            \
                ▼              ▼
        Primary Region   Secondary Region
              │                │
             ALB              ALB
              │                │
             App              App
              │                │
             DB  ──replication─► DB
```

The important point is that failover must include the complete dependency chain.

For a Django or FastAPI application, this can include:

```text
CloudFront
    ↓
ALB
    ↓
Application
    ↓
PostgreSQL
    ↓
Redis
    ↓
Kafka / Celery / External APIs
```

If a critical dependency remains unavailable in the secondary environment, the failover architecture may not meet the intended availability objective.

## Configuration Example

A conceptual origin-group configuration can be represented as:

```text
Origin Group: api-production

Primary:
    api-primary.example.internal

Secondary:
    api-secondary.example.internal

Failover Responses:
    500
    502
    503
    504
```

The exact configuration should be managed through infrastructure as code in production.

The important architectural properties are:

```text
Cache Behavior
      │
      ▼
Origin Group
      │
      ├── Primary
      └── Secondary
```

## AWS CLI Inspection

When troubleshooting an existing distribution, inspect its configuration through the AWS CLI.

```bash
aws cloudfront get-distribution-config \
  --id E123EXAMPLE
```

The returned configuration can be examined for:

- Origins.
- Origin groups.
- Cache behaviors.
- Failover configuration.
- Policies.
- Viewer protocol settings.

To inspect a distribution in a controlled environment, store the response rather than repeatedly querying the console:

```bash
aws cloudfront get-distribution-config \
  --id E123EXAMPLE \
  --output json > cloudfront-config.json
```

The exact distribution ID and account/region context should come from the environment being investigated.

## Testing Failover

Failover should be tested deliberately.

A useful test sequence is:

```text
1. Confirm primary works.
2. Confirm secondary works independently.
3. Generate representative requests.
4. Introduce controlled primary failure.
5. Confirm CloudFront uses the secondary.
6. Verify response correctness.
7. Measure failover latency.
8. Restore primary.
9. Verify recovery.
10. Confirm no unexpected data divergence.
```

Test more than a single `GET /health` request.

For an API, test realistic operations:

```text
GET /products/123
GET /orders/123
GET /users/me
```

For state-changing operations, test carefully because retries and duplicate side effects can occur.

## Failure Injection

A production-grade resilience strategy should use controlled failure testing where appropriate.

Possible scenarios include:

- Primary ALB unavailable.
- Application returning 503.
- Application returning 504.
- Database unavailable.
- Network path failure.
- Incorrect deployment.
- Regional dependency failure.

The purpose is to verify the complete path:

```text
Failure
   ↓
Detection
   ↓
CloudFront failover
   ↓
Secondary request
   ↓
Valid response
   ↓
Monitoring / alerting
```

## Common Mistakes

### Treating Origin Groups as Load Balancing

Origin groups are primarily for failover, not normal traffic distribution.

**Avoid it:** Use ALB or another appropriate load-balancing mechanism for healthy-target distribution.

### Making the Secondary Origin Incomplete

A secondary application that cannot access required data is not a real fallback.

**Avoid it:** Validate the entire dependency chain.

### Failing Over Non-Idempotent Writes Carelessly

A failed `POST` can have already created a resource.

**Avoid it:** Use idempotency keys and carefully evaluate whether write requests should participate in automatic failover.

### Using Too Many Failover Status Codes

A normal application response such as `404` may accidentally trigger failover.

**Avoid it:** Select failure statuses based on actual failure semantics.

### Assuming Failover Is Instant

The primary request must fail according to the configured criteria before CloudFront can use the secondary.

**Avoid it:** Include failover latency in RTO calculations.

### Ignoring Cached Errors

Error caching can make a temporary failure appear persistent.

**Avoid it:** Understand error-caching configuration and test recovery behavior.

### Assuming a Healthy ALB Means a Healthy Region

The application or its database may still be unavailable.

**Avoid it:** Use end-to-end readiness and dependency monitoring.

### Allowing Security Drift

The secondary origin may accidentally have weaker security controls.

**Avoid it:** Keep authentication, authorization, TLS, access controls, and security configuration consistent.

### Never Testing Failover

A configured origin group can still fail operationally because of an incorrect path, policy, security rule, or incomplete secondary environment.

**Avoid it:** Perform controlled failover exercises.

## Production Best Practices

### Keep Primary and Secondary Contract-Compatible

Both origins should expose compatible:

- URLs.
- HTTP methods.
- Response formats.
- Authentication.
- Authorization.
- Required headers.
- Content.

### Prefer Idempotent Operations for Automatic Failover

Failover is easiest to reason about for read operations.

For writes, use explicit idempotency and carefully defined recovery semantics.

### Minimize Shared Failure Domains

If both origins depend on the same unavailable resource, failover may not improve availability.

### Monitor Failover Traffic Separately

A successful secondary response is still an operational degradation if the primary is expected to be active.

### Test Recovery as Well as Failure

A system that fails over but cannot safely fail back is incomplete.

### Keep Configuration Consistent

Use infrastructure as code and CI/CD to prevent configuration drift between primary and secondary environments.

### Define Business-Level Recovery Requirements

Choose the architecture based on:

- RTO.
- RPO.
- Availability requirements.
- Data consistency requirements.
- Cost constraints.

Do not choose origin failover merely because it is technically available.

## Production Checklist

- [ ] Primary and secondary origins are explicitly defined.
- [ ] The origin group is attached to the correct cache behavior.
- [ ] Failover status codes are intentionally selected.
- [ ] Primary and secondary origins expose compatible interfaces.
- [ ] Secondary origin has the required application data.
- [ ] Required databases are available during failover.
- [ ] Authentication works on both origins.
- [ ] Authorization behavior is consistent.
- [ ] TLS is correctly configured.
- [ ] Origin access controls are equivalent.
- [ ] Read operations have been tested during failover.
- [ ] Non-idempotent writes have explicit retry/idempotency semantics.
- [ ] Error caching behavior is understood.
- [ ] Failover latency has been measured.
- [ ] Secondary-origin traffic is monitored.
- [ ] Primary recovery has been tested.
- [ ] Failback has been tested.
- [ ] RTO and RPO requirements are documented.
- [ ] Shared failure domains have been identified.
- [ ] Configuration is managed through version-controlled infrastructure as code.
- [ ] Controlled failure testing has been performed.

## Interview Traps

### Is an Origin Group the Same as Multiple Origins?

No.

A distribution can have multiple origins for different workloads. An origin group specifically defines a failover relationship between origins.

### Does CloudFront Continuously Health-Check the Primary and Automatically Switch Everything?

No.

Failover is based on the configured origin-group behavior and responses to viewer requests. It should not be confused with an independent application health-check and global traffic-management system.

### Does the Secondary Receive Traffic Normally?

Not as a normal load-balanced peer in the primary/secondary failover model. It is intended to serve as a fallback when the primary encounters configured failover conditions.

### Can Origin Groups Replace an ALB?

No.

An ALB distributes traffic among backend targets and provides application-origin load balancing. An origin group provides a higher-level fallback between origins.

### Does Origin Failover Solve Database Failover?

No.

CloudFront can redirect the request to another origin, but database replication, promotion, consistency, and recovery must be designed separately.

### Is Two-Region Application Deployment Automatically Disaster Recovery?

No.

A true DR architecture must consider application, database, storage, messaging, secrets, external dependencies, deployment, observability, and recovery procedures.

## Key Takeaways

- **Origin groups provide primary-to-secondary failover, not general-purpose load balancing:** use ALB or equivalent mechanisms to distribute traffic among healthy application targets.
- **Failover depends on configured HTTP failure conditions:** choose status codes carefully because legitimate application responses can otherwise trigger unnecessary secondary-origin requests.
- **The secondary origin must be operationally equivalent enough to serve the failed workload:** application code, authentication, data, dependencies, security controls, and configuration all matter.
- **Automatic failover is safest for idempotent operations:** state-changing requests require explicit idempotency and duplicate-side-effect protection.
- **CloudFront failover is only one part of disaster recovery:** RTO, RPO, database resilience, dependency availability, observability, testing, and failback must be designed as a complete system.