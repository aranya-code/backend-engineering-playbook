# 05- High Availability and Multi-Region Architecture

## Overview

CloudFront improves availability by placing an AWS-managed edge layer between clients and application origins. However, CloudFront itself does not make an application multi-region. High availability depends on the entire request and dependency path, including compute, databases, storage, messaging, authentication, and deployment infrastructure.

A production multi-region architecture typically separates two concerns:

- **Edge availability** — CloudFront continues accepting and routing viewer requests.
- **Origin availability** — an alternative application environment can successfully serve those requests when the primary environment is unavailable.

A simplified architecture is:

```text
                         Global Clients
                              │
                              ▼
                         CloudFront
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
             Primary Region       Secondary Region
                    │                   │
                   ALB                 ALB
                    │                   │
             Django / FastAPI    Django / FastAPI
                    │                   │
                 Database          Database
```

The critical engineering question is not whether two regions exist. It is whether the secondary region can independently satisfy the application's availability requirements when the primary region fails.

## Availability Model

Availability should be considered as a chain of dependencies rather than a property of a single AWS service.

For a backend application:

```text
Client
  ↓
CloudFront
  ↓
Origin
  ↓
Load Balancer
  ↓
Application
  ↓
Database
  ↓
Cache / Queue / External Services
```

If any critical component remains a single failure domain, the overall system may still have a single point of failure.

For example:

```text
CloudFront
   │
   ├── Region A App ──┐
   │                  │
   └── Region B App ──┤
                      ▼
                 One Database
```

The application tier is multi-region, but the database is not. A database outage can therefore still affect both regions.

## High Availability vs Disaster Recovery

These concepts should not be conflated.

| Concern | High Availability | Disaster Recovery |
|---|---|---|
| Goal | Minimize service interruption | Recover from major failure |
| Typical failure | Instance, AZ, service degradation | Region, data center, major dependency |
| Recovery | Usually automatic | Often partially automated |
| RTO | Very low | Defined by business requirement |
| RPO | Often near-zero | Depends on replication strategy |
| Secondary environment | Usually active | Can be warm or cold |
| Cost | Higher | Depends on standby strategy |

A multi-region architecture can provide both HA and DR, but only if the application and data layers are designed accordingly.

## Why Multi-Region Architecture Matters

A single AWS Region can contain multiple Availability Zones, providing strong resilience against many infrastructure failures.

A typical single-region architecture might be:

```text
CloudFront
    │
    ▼
ALB
    │
    ├── AZ-A → App
    ├── AZ-B → App
    └── AZ-C → App
```

This protects against many Availability Zone failures.

However, a regional failure is a larger fault domain:

```text
Region A
├── ALB
├── Compute
├── Database
└── Supporting services
        │
        └── Regional outage
```

A multi-region design introduces an independent environment:

```text
Region A                         Region B
────────                         ────────
ALB                              ALB
App                              App
DB                               DB
```

The architectural objective is to prevent one region from being a mandatory dependency for the other.

## CloudFront as the Global Entry Point

CloudFront can act as the global entry point for applications that need edge distribution and origin failover.

```mermaid
flowchart TD
    Users[Global Clients] --> CF[CloudFront Distribution]

    CF --> Primary[Primary Region]
    CF --> Secondary[Secondary Region]

    Primary --> ALB1[Application Load Balancer]
    ALB1 --> App1[Django / FastAPI]

    Secondary --> ALB2[Application Load Balancer]
    ALB2 --> App2[Django / FastAPI]
```

This architecture has several advantages:

- Clients use a stable global endpoint.
- Edge locations terminate viewer connections.
- CloudFront can cache content.
- Origin failover can reduce downtime.
- The application does not need to expose every regional origin publicly.

However, CloudFront does not automatically solve regional state, data consistency, or dependency recovery.

## Active-Passive Architecture

The simplest multi-region design is active-passive.

```text
                    CloudFront
                        │
                        ▼
                  Primary Region
                        │
                   Application
                        │
                    Database

                  Secondary Region
                        │
                 Standby Application
                        │
                Replicated / Backup DB
```

The primary handles normal traffic.

The secondary exists primarily for recovery.

### When to Use It

Active-passive is appropriate when:

- The workload can tolerate a controlled failover.
- The secondary environment does not need to serve normal production traffic.
- Cost is more important than maximum availability.
- Recovery procedures can tolerate some operational intervention.

### Advantages

- Lower cost than active-active.
- Easier state management.
- Easier deployment coordination.
- Simpler write semantics.
- Lower risk of conflicting writes.

### Limitations

- Secondary capacity may not be exercised regularly.
- Failover can expose configuration drift.
- Recovery may take longer.
- Secondary capacity may be insufficient during a sudden outage.

The secondary environment must still be tested regularly. An untested standby is not a reliable DR strategy.

## Active-Active Architecture

In an active-active architecture, both regions serve production traffic.

```text
                         CloudFront
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                 Region A        Region B
                    │               │
                   ALB             ALB
                    │               │
                  App A           App B
                    │               │
                   DB A           DB B
```

Traffic can be distributed between regions using an appropriate global routing strategy.

CloudFront origin configuration can participate in this architecture, but origin groups themselves should not be mistaken for a general-purpose active-active traffic distribution mechanism.

### Advantages

- Both regions continuously receive production traffic.
- Capacity is already exercised.
- Failover can be faster.
- Better resource utilization.

### Limitations

- More expensive.
- More complex data consistency.
- More difficult deployments.
- More complex background processing.
- Greater risk of split-brain behavior.
- Requires careful handling of writes.

Active-active is primarily a **distributed-systems problem**, not simply an AWS configuration problem.

## Active-Passive vs Active-Active

| Dimension | Active-Passive | Active-Active |
|---|---|---|
| Normal traffic | One region | Multiple regions |
| Cost | Lower | Higher |
| Operational complexity | Lower | Higher |
| Failover speed | Moderate to fast | Potentially very fast |
| Data consistency | Easier | Harder |
| Capacity utilization | Lower | Higher |
| Deployment complexity | Lower | Higher |
| Write conflicts | Less likely | Possible |
| Best fit | DR-focused workloads | High-availability global workloads |

## Multi-AZ vs Multi-Region

Multi-region should not replace multi-AZ design.

A robust architecture normally uses both:

```text
                     CloudFront
                         │
              ┌──────────┴──────────┐
              │                     │
           Region A              Region B
              │                     │
             ALB                   ALB
              │                     │
        ┌─────┴─────┐         ┌─────┴─────┐
       AZ-A        AZ-B       AZ-A        AZ-B
        │            │         │            │
       App          App       App          App
```

Multi-AZ protects against localized infrastructure failures.

Multi-region protects against larger regional failures.

The two strategies solve different failure domains.

## Region Selection

Multi-region architecture should not be designed around arbitrary region selection.

Consider:

- User geography.
- Application latency.
- AWS service availability.
- Data residency requirements.
- Compliance.
- Cross-region network latency.
- Replication capabilities.
- Cost.
- Disaster scenarios.

For an application serving users primarily from India, for example, a production design might evaluate AWS regions based on latency and compliance rather than simply selecting two geographically distant regions.

The important engineering property is that the regions should have sufficiently independent failure domains.

## Origin Architecture

A typical CloudFront multi-region setup can use regional ALBs as origins.

```text
CloudFront
    │
    ▼
Origin Group
    │
    ├── Primary → ALB Region A
    │                 │
    │                 ▼
    │              App Tier
    │
    └── Secondary → ALB Region B
                      │
                      ▼
                   App Tier
```

The ALB then provides intra-region load balancing:

```text
ALB
 │
 ├── App Instance A
 ├── App Instance B
 └── App Instance C
```

This gives separate responsibilities:

| Layer | Responsibility |
|---|---|
| CloudFront | Global edge delivery |
| Origin group | Primary/secondary origin failover |
| ALB | Regional traffic distribution |
| Application | Business logic |
| Database | Persistent state |

## Application Statelessness

Stateless application servers simplify multi-region architecture.

For Django or FastAPI:

```text
Region A
  ├── App 1
  ├── App 2
  └── App 3

Region B
  ├── App 1
  ├── App 2
  └── App 3
```

Application instances should avoid storing critical state locally.

Avoid relying on:

- Local filesystem state.
- In-memory session state.
- Local process caches for authoritative data.
- Instance-specific configuration.
- Local uploaded files.

Prefer shared or replicated services such as:

- S3 for object storage.
- Redis for appropriate ephemeral/shared caching.
- PostgreSQL for persistent relational state.
- Externalized secrets and configuration.

Statelessness does not eliminate distributed-state problems, but it reduces unnecessary coupling between application instances.

## Django and FastAPI Considerations

A multi-region Django or FastAPI application should externalize configuration and state.

For example:

```text
Application Container
       │
       ├── Environment/config
       ├── Secrets
       ├── Database connection
       ├── Redis connection
       └── Object storage
```

The same application artifact can then be deployed to both regions:

```text
Docker Image
     │
     ├── Region A
     └── Region B
```

This is preferable to maintaining different application builds for each region.

## Database Architecture

The database is usually the hardest component in multi-region architecture.

A naive design is:

```text
Region A App ──► Region A DB

Region B App ──► Region B DB
```

The challenge becomes:

```text
How do DB A and DB B stay consistent?
```

Possible approaches include:

- Primary/replica architectures.
- Cross-region database replication.
- Managed database global architectures.
- Application-level replication.
- Event-driven synchronization.
- Backup-and-restore DR.

The correct choice depends on:

- Read/write patterns.
- Consistency requirements.
- RPO.
- RTO.
- Transaction semantics.
- Data volume.

## Single-Writer Architecture

A common approach is to maintain one authoritative write region.

```text
Region A
   │
   ├── Application
   └── Primary Database
            │
            │ replication
            ▼
Region B
   │
   └── Secondary Database
```

This reduces write conflicts.

However, if Region A fails, Region B must eventually be promoted to accept writes.

That promotion process becomes part of the disaster-recovery architecture.

## Multi-Writer Architecture

Multi-writer systems allow both regions to accept writes.

```text
Region A ──► DB A
               │
               │ replication
               ▼
Region B ──► DB B
               │
               │ replication
               ▼
             DB A
```

This can provide excellent availability but introduces conflict resolution.

For example:

```text
Region A:
user.email = "a@example.com"

Region B:
user.email = "b@example.com"
```

If both writes happen concurrently, the system needs a deterministic conflict policy.

Multi-writer databases should therefore be selected because their consistency model matches the application, not simply because they provide multi-region capabilities.

## Redis in Multi-Region Architectures

Redis should be classified by the type of state it contains.

If Redis is only used as a cache:

```text
PostgreSQL
    │
    ▼
Application
    │
    ▼
Redis
```

a regional Redis outage may be survivable if the application can fall back to PostgreSQL.

For example:

```text
Redis unavailable
      │
      ▼
Cache miss
      │
      ▼
PostgreSQL
```

If Redis contains authoritative application state, distributed recovery becomes significantly more complex.

Do not assume that "Redis is replicated" means the application's state model is automatically safe across regions.

## Object Storage

Static assets and user-uploaded objects are often better candidates for cross-region resilience.

A common architecture is:

```text
Application
    │
    ▼
S3
    │
    └── Replication
          │
          ▼
       S3 Region B
```

CloudFront can then serve objects through the edge layer.

For applications using Django, media and static files should generally not depend on the local filesystem of an application instance.

## Kafka and Multi-Region Processing

Kafka introduces another distributed-system boundary.

Consider:

```text
Region A
   │
 Kafka A
   │
   ▼
Consumers

Region B
   │
 Kafka B
   │
   ▼
Consumers
```

If both regions process the same business events, the system must define:

- Event ownership.
- Consumer ownership.
- Duplicate processing behavior.
- Ordering requirements.
- Cross-region replication.
- Failover behavior.

For Celery-based systems, the same principle applies to task execution.

A multi-region application must define what happens to queued work when the primary region fails.

## Background Job Failover

Suppose:

```text
Primary Region
    │
    ▼
Celery
    │
    ▼
Payment Processing
```

If the region fails while a task is executing, the task may be:

- Lost.
- Retried.
- Replayed.
- Partially completed.

This creates the same idempotency problem discussed for HTTP writes.

Use idempotency keys or business-level deduplication for operations where duplicate processing is dangerous.

## Authentication and Sessions

Authentication must also be designed for multi-region operation.

Avoid:

```text
Region A
   │
   └── Local session storage
```

if users can be routed to Region B.

Better options may include:

- Stateless signed tokens.
- Shared session storage.
- Region-independent identity providers.
- Replicated authentication state.

For example:

```text
Client
   │
   ▼
CloudFront
   │
   ├── Region A
   └── Region B
        │
        ▼
   Shared Identity System
```

The authentication design must remain valid regardless of which region serves the request.

## CloudFront Cache During Regional Failures

CloudFront caching can provide an important resilience layer.

```text
Client
  │
  ▼
CloudFront
  │
  └── Cache Hit
       │
       └── No origin request
```

If an origin becomes unavailable, already-cached content may continue to be served.

This is particularly useful for:

- Static assets.
- Images.
- JavaScript bundles.
- CSS.
- Public documentation.
- Public read-only content.

However, cache should not be treated as a replacement for origin redundancy.

Dynamic uncached requests still require a functioning origin.

## Cache Strategy for High Availability

A useful architecture separates static and dynamic traffic:

```text
CloudFront
    │
    ├── /static/* ──► S3
    │
    ├── /media/* ───► S3
    │
    └── /api/* ─────► Multi-Region API
```

Static content can have long TTLs:

```text
/static/app.8f32c.js
```

while APIs may use much shorter or carefully controlled caching.

Content-addressed asset names are particularly useful because deployments can publish new immutable objects rather than relying on immediate cache invalidation.

## Deployment Architecture

Multi-region deployments should use the same versioned artifact.

```text
GitHub
   │
   ▼
CI/CD
   │
   ▼
Container Image
   │
   ├── Region A
   └── Region B
```

For example:

```text
ghcr.io/company/api:2026.08.19-abc123
```

Both regions should receive the same tested artifact unless there is a deliberate compatibility reason not to.

This reduces configuration drift.

## Deployment Strategies

Useful strategies include:

- Rolling deployments.
- Blue/green deployments.
- Canary deployments.
- Region-by-region deployment.
- Shadow traffic.

A safe regional deployment sequence may be:

```text
Build
  ↓
Test
  ↓
Deploy Region B
  ↓
Validate
  ↓
Deploy Region A
  ↓
Validate
```

The exact order depends on traffic distribution and rollback requirements.

## Infrastructure as Code

Multi-region infrastructure should be managed through version-controlled infrastructure as code.

The same logical configuration should be reproducible across regions.

For example:

```text
infrastructure/
├── cloudfront/
├── network/
├── application/
├── database/
└── observability/
```

Region-specific values should be explicit rather than duplicated through manual console configuration.

This reduces configuration drift between primary and secondary environments.

## Failure Domains

A senior architecture review should identify every failure domain.

| Layer | Example Failure Domain |
|---|---|
| Client | ISP/network |
| CloudFront | Distribution/configuration |
| Region | Regional outage |
| AZ | Availability Zone |
| ALB | Load balancer |
| Compute | Instance/node |
| Database | Cluster/region |
| Redis | Cache cluster |
| Kafka | Broker/cluster |
| External API | Third-party provider |
| CI/CD | Deployment system |

The objective is not to eliminate every failure. The objective is to ensure that important failures do not exceed the system's defined recovery objectives.

## RTO and RPO

Multi-region design should begin with business requirements.

### Recovery Time Objective

RTO answers:

> How long can the system be unavailable?

Example:

```text
RTO = 5 minutes
```

### Recovery Point Objective

RPO answers:

> How much data loss is acceptable?

Example:

```text
RPO = 1 minute
```

A system requiring:

```text
RTO = 5 minutes
RPO = near-zero
```

requires significantly more engineering than:

```text
RTO = 24 hours
RPO = 24 hours
```

CloudFront can reduce part of the traffic-routing recovery path, but it does not determine the database RPO or application recovery time.

## Failure Scenario

Consider a regional outage:

```mermaid
sequenceDiagram
    participant User
    participant CF as CloudFront
    participant Primary
    participant Secondary

    User->>CF: GET /api/products/123
    CF->>Primary: Request
    Primary--xCF: 503 / timeout
    CF->>Secondary: Failover request
    Secondary-->>CF: 200 OK
    CF-->>User: 200 OK
```

This looks simple, but the secondary must already have:

- Application capacity.
- Required configuration.
- Secrets.
- Data.
- Authentication.
- External dependencies.
- Observability.
- Correct routing.

Otherwise:

```text
Primary fails
    ↓
CloudFront fails over
    ↓
Secondary fails
    ↓
Outage continues
```

## Shared Dependencies

One of the most important multi-region design checks is identifying shared dependencies.

For example:

```text
Region A ──┐
           ├──► One external payment provider
Region B ──┘
```

If the payment provider is down globally, regional redundancy does not solve the problem.

Similarly:

```text
Region A ──┐
           ├──► One authentication provider
Region B ──┘
```

can remain a global failure domain.

Document shared dependencies explicitly.

## Security Considerations

Both regions should have equivalent security controls.

Verify:

- IAM roles.
- Security groups.
- Network ACLs where applicable.
- TLS configuration.
- WAF configuration.
- Secrets.
- KMS permissions.
- Database encryption.
- S3 access controls.
- Origin access controls.
- Authentication.
- Authorization.

A secondary region should never be treated as a lower-security environment simply because it is primarily used for DR.

## Origin Protection

The architecture should prevent unintended direct access to regional origins where appropriate.

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Regional ALB
```

If the ALB is directly reachable from the public internet, clients may bypass CloudFront's edge controls.

Depending on the architecture, use appropriate AWS networking and origin-protection mechanisms so that traffic follows the intended path.

## Monitoring and Observability

Multi-region systems require region-aware observability.

A dashboard should distinguish:

```text
Region A
├── Request rate
├── Latency
├── 4xx
├── 5xx
└── Dependency health

Region B
├── Request rate
├── Latency
├── 4xx
├── 5xx
└── Dependency health
```

CloudFront metrics should be correlated with origin metrics.

For example:

```text
CloudFront 5xx ↑
       │
       ▼
Primary ALB 5xx ↑
       │
       ▼
PostgreSQL errors ↑
```

This provides a much stronger diagnosis than observing only the CloudFront metric.

## Detecting Degraded State

A system can be technically available while degraded.

Example:

```text
Primary Region: 0% traffic
Secondary Region: 100% traffic
Viewer 200 rate: 99.99%
```

The customer may still be receiving successful responses, but the architecture is operating outside its intended normal state.

Alert on:

- Unexpected secondary traffic.
- Regional traffic imbalance.
- Primary-origin failure.
- Cross-region replication lag.
- Database promotion.
- Failover activation.
- Secondary capacity exhaustion.

## Capacity Planning

The secondary region must have enough capacity for its intended role.

For active-passive:

```text
Primary capacity = 100%
Secondary capacity = 40%
```

may be acceptable only if the recovery plan explicitly allows scaling the secondary before or during failover.

For active-active:

```text
Region A = 50%
Region B = 50%
```

a regional failure may cause:

```text
Region B = 100%
```

Therefore, each region must have sufficient headroom.

A useful principle is:

> Design capacity for the failure state, not only the healthy state.

## Cost Considerations

Multi-region architecture increases cost through:

- Additional compute.
- Additional load balancers.
- Database replication.
- Cross-region data transfer.
- Additional Redis/Kafka infrastructure.
- Additional monitoring.
- Additional deployment infrastructure.

Active-passive can reduce compute cost but may require faster scaling during recovery.

Active-active costs more but keeps capacity exercised continuously.

Cost should be evaluated against:

- RTO.
- RPO.
- Availability SLA.
- Revenue impact of downtime.
- Regulatory requirements.
- Operational complexity.

## Disaster Recovery Testing

A DR architecture is incomplete until it is tested.

Testing should include:

```text
Primary Region Failure
        ↓
CloudFront / routing behavior
        ↓
Secondary Region
        ↓
Database availability
        ↓
Authentication
        ↓
Background jobs
        ↓
External dependencies
        ↓
Application correctness
```

Test recovery, not only infrastructure availability.

A successful ALB health check is insufficient if:

```text
GET /api/orders
```

fails because the database has not been promoted.

## Failback

Failback is the process of returning traffic to the primary region after recovery.

A safe sequence is:

```text
Primary repaired
      ↓
Data synchronized
      ↓
Application validated
      ↓
Capacity validated
      ↓
Controlled traffic restoration
      ↓
Primary receives normal traffic
      ↓
Secondary returns to standby/normal state
```

Do not immediately send 100% of traffic back to a recently recovered region.

A controlled transition reduces the risk of a second outage.

## Common Mistakes

### Treating CloudFront as the Entire DR Strategy

CloudFront can provide edge routing and caching, but it does not replicate databases or application state.

**Avoid it:** Design DR across the entire dependency graph.

### Building Two Regions With One Database

Two application regions do not provide complete regional resilience if both depend on one database failure domain.

**Avoid it:** Explicitly design database replication, promotion, backup, and recovery.

### Using Active-Active Without Conflict Semantics

Two regions accepting writes can create conflicting updates.

**Avoid it:** Define ownership, consistency, conflict resolution, and idempotency before implementing multi-writer behavior.

### Under-Provisioning the Secondary Region

A secondary region that cannot handle production traffic is not a valid failover target.

**Avoid it:** Load-test the recovery capacity.

### Letting Configuration Drift

The primary may have:

```text
App version: 1.8
```

while the secondary has:

```text
App version: 1.5
```

Failover can then expose incompatible behavior.

**Avoid it:** Use the same versioned artifacts and infrastructure-as-code workflows.

### Forgetting Background Processing

The HTTP API may fail over successfully while Celery or Kafka processing remains unavailable.

**Avoid it:** Include asynchronous workloads in the DR design.

### Ignoring Authentication

Users may reach the secondary region but fail authentication because session or identity state is region-specific.

**Avoid it:** Make authentication state available independently of the serving region.

### Assuming Cache Solves Dynamic Availability

CloudFront may continue serving cached assets while API requests fail.

**Avoid it:** Evaluate static and dynamic availability separately.

### Never Testing Regional Failure

A design that has never been exercised may contain hidden assumptions.

**Avoid it:** Perform controlled DR and failover exercises.

## Production Best Practices

### Keep Application Artifacts Identical

Build once and deploy the same immutable artifact across regions.

### Minimize Regional State

Keep application instances stateless wherever practical.

### Separate Static and Dynamic Traffic

Use CloudFront caching and object storage aggressively for static content while designing dynamic APIs for independent origin resilience.

### Define Data Ownership

For every database or stateful system, document:

- Primary writer.
- Replicas.
- Replication method.
- Promotion mechanism.
- RPO.
- Recovery procedure.

### Design for Failure Capacity

Ensure the surviving region can handle the expected traffic after failover.

### Automate Recovery Where Practical

Automate:

- Infrastructure provisioning.
- Deployment.
- Database promotion where safe.
- Configuration.
- Monitoring.
- Failover validation.

Keep human approval for high-risk state transitions when necessary.

### Test the Full Dependency Chain

Do not stop at CloudFront or ALB.

Test:

```text
CloudFront
 → ALB
 → Application
 → Database
 → Redis
 → Kafka/Celery
 → External APIs
```

### Monitor the Failure State

Alert when the secondary region is unexpectedly serving production traffic even if viewer requests remain successful.

### Define Explicit Recovery Objectives

Architecture decisions should map to measurable:

- RTO.
- RPO.
- Availability targets.

## Production Checklist

- [ ] CloudFront is the intended global entry point.
- [ ] Primary and secondary origins are independently deployable.
- [ ] Both regions use compatible application versions.
- [ ] Multi-AZ resilience exists within each region.
- [ ] Secondary capacity is sufficient for the expected failover load.
- [ ] Database replication and promotion are explicitly designed.
- [ ] RPO is documented.
- [ ] RTO is documented.
- [ ] Authentication works independently of the primary region.
- [ ] Redis dependency behavior is defined.
- [ ] Kafka/Celery failover behavior is defined.
- [ ] Object storage is replicated or recoverable.
- [ ] External dependencies have been identified.
- [ ] Security controls are equivalent across regions.
- [ ] WAF and origin-protection configuration is consistent.
- [ ] Infrastructure is managed as code.
- [ ] CI/CD deploys consistent artifacts.
- [ ] CloudFront failover has been tested.
- [ ] Database recovery has been tested.
- [ ] Background-job recovery has been tested.
- [ ] Failback has been tested.
- [ ] Regional failure drills are performed periodically.
- [ ] Monitoring distinguishes normal, degraded, and failed states.

## Interview Traps

### Does CloudFront Make an Application Multi-Region?

No. CloudFront provides the global edge layer. The origins and their dependencies must independently exist and operate across regions.

### Is Multi-AZ the Same as Multi-Region?

No. Multi-AZ protects against Availability Zone failures within a region. Multi-region protects against larger regional failure domains.

### Is Active-Active Always Better?

No. Active-active provides stronger utilization and potentially faster failover but significantly increases state-management and consistency complexity.

### Can Two Application Regions Share One Database?

They can, but that database remains a shared failure domain. It may therefore prevent the architecture from meeting true regional-failure requirements.

### Does Multi-Region Eliminate Downtime?

No. It reduces the impact of specific failure scenarios. Recovery still depends on routing, application compatibility, data availability, dependencies, and operational procedures.

### Does a Replicated Database Mean Zero Data Loss?

Not necessarily. Replication lag, asynchronous replication, promotion semantics, and transaction behavior determine the actual RPO.

### Can CloudFront Replace Application-Level Failover Logic?

No. CloudFront can redirect requests between origins, but application retries, idempotency, database recovery, queue processing, and business-level consistency remain application concerns.

## Key Takeaways

- **CloudFront provides the global edge layer, not complete multi-region resilience:** availability must be designed across compute, data, storage, messaging, authentication, and external dependencies.
- **Multi-AZ and multi-region solve different failure domains:** robust production systems commonly use both rather than treating them as alternatives.
- **Active-passive simplifies state management while active-active improves utilization and failover speed:** the correct model depends on RTO, RPO, consistency, and cost requirements.
- **The database and asynchronous workloads are usually the hardest parts of multi-region design:** replication, promotion, idempotency, queue ownership, and duplicate processing must be explicitly designed.
- **A DR architecture is only credible when it is tested:** validate regional failure, application recovery, data recovery, background processing, observability, capacity, and failback rather than relying on configuration alone.