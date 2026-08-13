# 09- Architect Level Questions

## Overview

Architect-level Elastic Beanstalk questions evaluate whether an engineer can make and defend system-level decisions rather than simply operate an Elastic Beanstalk environment.

The expected reasoning extends beyond:

- How to deploy an application.
- How to configure Auto Scaling.
- How to change environment variables.
- How to select a deployment policy.

Architect-level discussions should cover:

- Service boundaries.
- Availability and failure domains.
- Scalability limits.
- Dependency bottlenecks.
- Deployment safety.
- Network architecture.
- Security boundaries.
- Data consistency.
- Disaster recovery.
- Observability.
- Cost.
- Operational ownership.
- Migration strategy.
- Platform suitability.

A strong architectural answer should make trade-offs explicit and identify what would cause the design to change.

## Architectural Role of Elastic Beanstalk

### How should Elastic Beanstalk be positioned in a production architecture?

Elastic Beanstalk should be viewed as an application platform rather than as an independent compute primitive.

The application runs on AWS infrastructure managed and orchestrated by Elastic Beanstalk, while the surrounding architecture may include services such as:

- Application Load Balancer.
- EC2 Auto Scaling.
- VPC.
- Amazon RDS or another database.
- ElastiCache or another cache.
- Amazon S3.
- CloudWatch.
- IAM.
- Secrets Manager.
- Route 53.
- SNS, SQS, or Kafka-based infrastructure where appropriate.

A typical architecture is:

```text
                         Users
                           |
                           v
                    Route 53 / DNS
                           |
                           v
                 Application Load Balancer
                           |
              +------------+------------+
              |                         |
              v                         v
       Availability Zone A       Availability Zone B
              |                         |
        EB EC2 Instance            EB EC2 Instance
              |                         |
              +------------+------------+
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          PostgreSQL     Redis          S3
             |
             v
        Persistent Data
```

Elastic Beanstalk provides the application deployment and environment management layer, but architectural responsibility remains with the engineering team.

### What responsibilities remain with the engineering team when using Elastic Beanstalk?

Managed infrastructure does not eliminate architectural responsibility.

The engineering team still owns:

- Application architecture.
- Application security.
- Database design.
- Connection management.
- Scaling policies.
- Deployment strategy.
- Runtime compatibility.
- Observability.
- Dependency management.
- Secret management.
- Disaster recovery.
- Capacity planning.
- Cost management.
- Incident response.

The important architectural distinction is:

> Managed infrastructure reduces operational work; it does not transfer responsibility for application behavior.

## Platform Selection

### When would you choose Elastic Beanstalk for a new backend system?

Elastic Beanstalk is a strong candidate when:

- The application follows a supported platform model.
- The workload is primarily web-based.
- The team wants managed deployment and scaling.
- The team does not require Kubernetes-level orchestration.
- Infrastructure customization requirements are moderate.
- Operational simplicity is a major priority.

For example, a Django application may be a good fit:

```text
Django
  |
  v
Elastic Beanstalk
  |
  +--> EC2 Auto Scaling
  +--> Load Balancer
  |
  +--> PostgreSQL
  +--> Redis
  +--> S3
```

The decision should be based on requirements rather than on the perceived sophistication of the platform.

### When would Elastic Beanstalk be the wrong architectural choice?

Potential reasons include:

| Requirement | Better consideration |
|---|---|
| Kubernetes-native platform | EKS |
| Container orchestration at scale | ECS or EKS |
| Event-driven serverless workload | Lambda / event-driven services |
| Highly specialized host configuration | EC2 or specialized infrastructure |
| Complex multi-service scheduling | ECS/EKS |
| Existing organization-wide Kubernetes platform | EKS |
| Very simple static workload | S3 + CloudFront |
| Highly customized infrastructure lifecycle | Infrastructure-as-code + lower-level services |

The key question is not:

> "Which AWS service is more powerful?"

It is:

> "Which platform satisfies the requirements with the lowest acceptable operational complexity?"

### How would you justify Elastic Beanstalk to an architecture review board?

A strong justification should identify:

1. Application requirements.
2. Operational requirements.
3. Availability requirements.
4. Scalability characteristics.
5. Security constraints.
6. Deployment requirements.
7. Team capabilities.
8. Expected growth.
9. Platform limitations.
10. Migration or replacement criteria.

For example:

> The application is a stateless Django API with conventional HTTP traffic, moderate scaling requirements, and no Kubernetes-specific requirements. Elastic Beanstalk provides the required load balancing, Auto Scaling, deployment automation, and runtime management while keeping operational complexity lower than introducing a Kubernetes platform.

That is stronger than saying:

> "Elastic Beanstalk is easier."

## High Availability Architecture

### How would you architect a highly available Elastic Beanstalk application?

The application tier should span multiple Availability Zones and use load balancing.

A broader architecture should look like:

```text
                         Internet
                            |
                            v
                         Route 53
                            |
                            v
                  Application Load Balancer
                     /               \
                    v                 v
              Availability A     Availability B
                    |                 |
                 EB EC2            EB EC2
                    |                 |
                    +--------+--------+
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
          Multi-AZ Database       Managed Redis
```

Important characteristics include:

- Multiple application instances.
- Multiple Availability Zones.
- Load balancing.
- Health checks.
- Stateless application design.
- Highly available persistent dependencies where required.
- Automated instance replacement.
- Centralized observability.

### Does running two Elastic Beanstalk instances guarantee high availability?

No.

Two instances in the same Availability Zone still share a failure domain.

Even multi-AZ application instances do not guarantee complete system availability if:

- The database is unavailable.
- Redis is unavailable.
- DNS configuration is incorrect.
- External dependencies fail.
- Deployment configuration is broken.
- Application health checks are incorrect.

High availability must be evaluated across the entire dependency graph.

### How would you design for Availability Zone failure?

The application tier should be distributed across multiple Availability Zones.

Persistent dependencies should have their own appropriate availability strategy.

For example:

```text
                   Load Balancer
                   /            \
                  /              \
               AZ-A              AZ-B
                |                  |
             App-A              App-B
                \                  /
                 \                /
                  +--------------+
                         |
                  Multi-AZ DB
```

The architecture should not rely on a single instance, subnet, or Availability Zone.

## Failure Domains

### What are the major failure domains in an Elastic Beanstalk architecture?

A production system can fail at several layers:

```text
User
 |
 v
DNS
 |
 v
Load Balancer
 |
 v
Application Instances
 |
 +---- Database
 |
 +---- Redis
 |
 +---- S3
 |
 +---- External APIs
 |
 +---- Messaging Systems
```

Each layer has different failure characteristics.

A senior architect should identify:

- Failure probability.
- Failure impact.
- Detection mechanism.
- Recovery mechanism.
- Blast radius.
- Whether the dependency is replaceable.

### How do you reduce blast radius?

Use isolation boundaries.

Examples include:

- Separate environments for staging and production.
- Separate AWS accounts where organizationally appropriate.
- Multi-AZ application placement.
- Least-privilege IAM.
- Independent deployment pipelines.
- Feature flags.
- Controlled database migrations.
- Service-level timeouts.
- Circuit breakers where appropriate.
- Queue-based workload isolation.

The goal is to prevent a local failure from becoming a system-wide outage.

## Stateless Architecture

### Why is statelessness especially important for Elastic Beanstalk?

Elastic Beanstalk environments may replace, add, or remove instances.

Therefore:

```text
Request 1 ---> Instance A
Request 2 ---> Instance B
Request 3 ---> Instance C
```

The application must not assume that the same instance will receive subsequent requests.

Persistent state should be externalized.

| State | Appropriate location |
|---|---|
| Business data | PostgreSQL / database |
| User-uploaded files | S3 |
| Shared cache | Redis |
| Shared sessions | Redis / database |
| Background jobs | Queue / task system |
| Instance logs | Centralized logging |
| Temporary files | Local disk only when disposable |

Local filesystem storage should generally be treated as ephemeral.

### Why are sticky sessions usually not the preferred solution?

Sticky sessions can preserve affinity between a client and a particular instance, but they reduce the flexibility of horizontal scaling.

They can also create problems when:

- An instance fails.
- Capacity changes.
- Deployments replace instances.
- Traffic distribution becomes uneven.

A better architecture is usually to externalize shared state so any instance can serve any request.

## Scaling Architecture

### How would you determine the correct Auto Scaling limits?

Do not choose minimum and maximum capacity arbitrarily.

Consider:

- Baseline traffic.
- Peak traffic.
- Request latency.
- CPU and memory utilization.
- Instance startup time.
- Database capacity.
- Redis capacity.
- External API limits.
- Cost constraints.
- Recovery requirements.

For example:

```text
Traffic
   |
   v
Application Scaling
   |
   v
More Instances
   |
   v
More DB Connections
   |
   v
Database Saturation
```

Application scaling is only useful if downstream dependencies can support the additional workload.

### What is the difference between application scalability and system scalability?

Application scalability means the application tier can handle increasing workload.

System scalability considers the entire architecture:

```text
Load Balancer
      |
Application
      |
Database
      |
Cache
      |
Messaging
      |
External Services
```

A Django API may scale from 5 to 50 instances while PostgreSQL cannot support the resulting connection and query volume.

Therefore:

> The scalable capacity of a system is constrained by its critical bottlenecks.

### How would you handle sudden traffic spikes?

Possible strategies include:

- Horizontal Auto Scaling.
- Appropriate instance sizing.
- Caching.
- CDN usage for static content.
- Database optimization.
- Queue-based asynchronous processing.
- Rate limiting.
- Load shedding.
- Backpressure.
- Capacity planning.

For expensive work:

```text
HTTP Request
    |
    v
Validate
    |
    v
Publish Job
    |
    v
Return Response
    |
    v
Worker
    |
    v
Database / External API
```

Moving expensive work out of the request path can protect application latency.

## Database Architecture

### How would you architect PostgreSQL for a highly available Elastic Beanstalk application?

Elastic Beanstalk should not be treated as the database platform.

A typical design is:

```text
Elastic Beanstalk
      |
      v
Application Layer
      |
      v
Managed PostgreSQL
      |
      +--> Backups
      +--> Multi-AZ capability
      +--> Monitoring
```

The database should have an independently designed:

- Availability strategy.
- Backup strategy.
- Recovery strategy.
- Capacity model.
- Security boundary.
- Maintenance strategy.

### What happens when Auto Scaling increases application instances but PostgreSQL cannot scale at the same rate?

The database becomes the bottleneck.

Symptoms may include:

- Connection exhaustion.
- Increased query latency.
- Lock contention.
- CPU saturation.
- Increased request latency.
- HTTP 5xx errors.

Architectural responses can include:

- Query optimization.
- Index optimization.
- Connection pooling.
- Worker tuning.
- Caching.
- Read replicas where appropriate.
- Database scaling.
- Workload partitioning.
- Asynchronous processing.

### How would you prevent a database connection storm?

Suppose:

```text
20 instances
x
4 workers
=
80 workers
```

If each worker establishes database connections, scaling can produce a large increase in concurrent database connections.

Mitigation includes:

- Controlled worker counts.
- Connection pooling.
- Database capacity planning.
- Appropriate connection lifetime settings.
- Controlled Auto Scaling.
- Avoiding unnecessary connection initialization.

Scaling policy and database capacity should be designed together.

## Caching Architecture

### Where would Redis fit into an Elastic Beanstalk architecture?

Redis can be used for:

- Frequently accessed data.
- Session storage.
- Rate limiting.
- Temporary state.
- Application-level caching.
- Distributed coordination where appropriate.

A typical flow is:

```text
Client
  |
  v
Elastic Beanstalk
  |
  +----> Redis ---- Cache Hit ----> Response
  |
  +----> PostgreSQL ---- Cache Miss
```

The architect must define:

- Cache key strategy.
- TTL.
- Invalidation.
- Maximum object size.
- Eviction behavior.
- Failure behavior.

### What should happen if Redis becomes unavailable?

The answer depends on what Redis stores.

If Redis is only a cache:

```text
Redis Failure
     |
     v
Cache Miss
     |
     v
Database
```

The application can potentially continue operating, although with increased database load.

If Redis stores critical session or coordination state, the failure model is more serious.

Therefore, architects should classify dependencies as:

- Critical.
- Degraded-but-functional.
- Optional.

## Deployment Architecture

### How would you design deployments for a business-critical application?

A mature deployment architecture may use:

```text
Source
  |
  v
CI/CD
  |
  v
Build Immutable Artifact
  |
  v
Automated Tests
  |
  v
Staging
  |
  v
Smoke / Integration Tests
  |
  v
Production Candidate
  |
  +--> Blue/Green
  |       |
  |       v
  |    Validation
  |
  v
Traffic Shift
  |
  v
Monitoring
  |
  +---- Failure ---> Rollback
```

The strategy should account for:

- Deployment duration.
- Rollback time.
- Database compatibility.
- Capacity requirements.
- Release frequency.
- Blast radius.

### When would you choose blue/green over rolling deployment?

Blue/green is useful when:

- Fast rollback is important.
- Release risk is high.
- Environment isolation is valuable.
- Temporary additional infrastructure cost is acceptable.

Rolling deployment may be preferred when:

- Capacity is constrained.
- The application supports mixed versions.
- Deployment risk is lower.
- Additional infrastructure is undesirable.

### Does blue/green solve database migration problems?

No.

Suppose version 2 requires a new schema:

```text
Blue ---> Database
Green --> Database
```

Both environments may still depend on the same database.

If Green requires schema changes incompatible with Blue, traffic switching alone does not solve the problem.

Use backward-compatible migrations:

```text
Expand
  |
  v
Deploy
  |
  v
Migrate Usage
  |
  v
Contract
```

## Data Migration Architecture

### How would you perform a large database migration without causing downtime?

Separate schema changes from application behavior.

A typical approach:

```text
Add New Schema
      |
      v
Deploy Compatible Code
      |
      v
Backfill Data
      |
      v
Switch Reads/Writes
      |
      v
Validate
      |
      v
Remove Old Schema
```

For large tables, consider:

- Batch processing.
- Lock duration.
- Index creation strategy.
- Replication impact.
- Database CPU.
- I/O.
- Application compatibility.

Avoid large blocking migrations during peak traffic.

### How would you handle a migration that cannot be rolled back?

Treat it as a forward-only change.

Before executing:

- Validate backups.
- Test restoration.
- Test migration duration.
- Measure database impact.
- Establish application rollback alternatives.
- Prepare compensating actions.

A deployment rollback is not the same thing as a database rollback.

## Security Architecture

### How would you design network security for Elastic Beanstalk?

A typical design is:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application Instances
   |
   v
Private Database
```

Security groups should define communication paths between tiers.

For example:

```text
ALB SG
  |
  v
Application SG
  |
  v
Database SG
```

The database should not generally accept traffic directly from the public internet.

### How would you apply least privilege?

Use separate identities for different responsibilities.

Examples:

- Application instance role.
- Deployment role.
- CI/CD role.
- Administrative role.

Avoid giving the application unrestricted AWS permissions.

A Django application that only uploads objects to one S3 bucket should not require broad administrative permissions.

### How would you protect secrets?

Use managed secret/configuration mechanisms and IAM-controlled access.

The architecture should avoid:

```text
Git Repository
    |
    +--> DATABASE_PASSWORD
    +--> AWS_SECRET_ACCESS_KEY
```

Instead:

```text
Application
    |
    v
IAM Role
    |
    v
Secret Store
    |
    v
Runtime Credential
```

Secrets should also be excluded from:

- Logs.
- Error messages.
- Debug output.
- Source control.
- Build artifacts.

## Observability Architecture

### What observability architecture would you use?

Observability should cover:

```text
                 Application
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
     Logs         Metrics        Traces
       |             |             |
       +-------------+-------------+
                     |
                     v
                Alerting
                     |
                     v
               Incident Response
```

Monitor:

- Request rate.
- Error rate.
- Latency.
- Saturation.
- Instance health.
- Deployment health.
- Database health.
- Cache health.
- Queue depth.
- Business-level success metrics.

### Why are health checks an architectural concern?

A health check determines whether the load balancer considers an instance capable of serving traffic.

A weak health check might return success even though critical dependencies are unavailable.

A health check that is too strict can also remove healthy instances during temporary dependency failures.

The architect must define what "healthy" means.

For example:

```text
Process alive?
      |
      v
Application responding?
      |
      v
Critical dependency available?
      |
      v
Accept traffic?
```

The answer should reflect the application's failure model.

## Reliability Engineering

### How should you design for graceful degradation?

Not every dependency failure should take down the entire service.

For example:

```text
Request
  |
  +---- Core Database ----> Required
  |
  +---- Redis ------------> Optional
  |
  +---- Recommendation API -> Optional
```

If recommendations fail, the core transaction may still succeed.

This requires explicit dependency classification.

### How would you implement timeouts for downstream services?

Every synchronous dependency should have bounded time.

For example:

```text
API
 |
 +---- PostgreSQL
 |
 +---- Redis
 |
 +---- External API
```

An external API that hangs indefinitely can consume application workers and eventually exhaust capacity.

Use:

- Connection timeouts.
- Read timeouts.
- Total request deadlines.
- Retry limits.
- Circuit breakers where appropriate.

Retries should also use backoff and should not blindly retry non-idempotent operations.

### How can retries make an outage worse?

Suppose an external service is already overloaded:

```text
Service Failure
      |
      v
Requests Timeout
      |
      v
Clients Retry
      |
      v
More Requests
      |
      v
More Overload
```

This creates a retry storm.

Architectural controls include:

- Exponential backoff.
- Jitter.
- Maximum retry counts.
- Circuit breakers.
- Idempotency.
- Queue-based processing.
- Rate limiting.

## Disaster Recovery Architecture

### How would you design disaster recovery for Elastic Beanstalk?

Separate recovery of compute from recovery of state.

```text
Application
    |
    +--> Reproducible Artifact
    |
    +--> Environment Configuration

Database
    |
    +--> Backup
    +--> Recovery Procedure

Object Storage
    |
    +--> Durable Data

Infrastructure
    |
    +--> Reproducible Configuration
```

The application tier should be reconstructable.

The database and persistent data require explicit recovery mechanisms.

### What are RTO and RPO?

**RTO — Recovery Time Objective**

How long the system can remain unavailable before recovery must be completed.

**RPO — Recovery Point Objective**

How much data loss, measured in time, is acceptable.

For example:

| Requirement | Target |
|---|---|
| RTO | 30 minutes |
| RPO | 5 minutes |

These targets influence:

- Backup frequency.
- Replication.
- Multi-region design.
- Automation.
- Operational cost.

### Would you deploy Elastic Beanstalk across multiple AWS Regions for disaster recovery?

Only when business requirements justify the complexity.

Multi-region architecture introduces:

- Data replication challenges.
- DNS or traffic-routing complexity.
- Configuration duplication.
- Secret replication.
- Deployment complexity.
- Higher cost.
- Operational complexity.

For many systems, multi-AZ architecture within one Region plus tested backups may be sufficient.

Architecture should follow RTO/RPO requirements rather than assuming multi-region is automatically better.

## Multi-Region Architecture

### How would you architect a multi-region Elastic Beanstalk application?

A conceptual architecture is:

```text
                     Global DNS
                         |
             +-----------+-----------+
             |                       |
             v                       v
          Region A                Region B
             |                       |
        Load Balancer            Load Balancer
             |                       |
        EB Application           EB Application
             |                       |
             +-----------+-----------+
                         |
                 Data Replication
```

The difficult part is usually not duplicating the application tier.

The difficult parts are:

- Database consistency.
- Write ownership.
- Data replication.
- Session management.
- Object storage.
- Cache behavior.
- Failover.
- DNS propagation.
- Operational coordination.

### Would you use active-active or active-passive?

It depends on business and consistency requirements.

| Strategy | Advantages | Trade-offs |
|---|---|---|
| Active-passive | Simpler data model | Failover capacity must be maintained |
| Active-active | Better utilization and potentially faster regional resilience | Much more complex consistency and routing |

For many systems, active-passive is easier to operate correctly.

## Messaging and Asynchronous Architecture

### When should you introduce asynchronous processing?

Use asynchronous processing when work:

- Takes significant time.
- Does not need to block the HTTP response.
- Can tolerate eventual processing.
- Needs retry semantics.
- Benefits from workload buffering.

Example:

```text
Client
  |
  v
Django API
  |
  v
Queue
  |
  +---- Worker 1
  +---- Worker 2
  +---- Worker 3
  |
  v
PostgreSQL / External Service
```

This can protect the HTTP tier from slow downstream operations.

### How does queue-based architecture improve resilience?

A queue can absorb temporary workload spikes.

```text
Traffic Spike
     |
     v
API
     |
     v
Queue  <--- Buffer
     |
     v
Workers
     |
     v
Dependency
```

The queue does not remove capacity limits. It changes the failure behavior from immediate request failure to delayed processing, assuming the business workflow permits that.

## Microservices Architecture

### Would you deploy each microservice into a separate Elastic Beanstalk environment?

Possibly, but not automatically.

Separate environments provide:

- Deployment isolation.
- Independent scaling.
- Failure isolation.
- Configuration isolation.

However, many environments also increase:

- Operational overhead.
- Cost.
- Configuration management.
- Monitoring complexity.
- Deployment complexity.

For a small system, a modular monolith may be operationally superior.

### How would you decide between a monolith and multiple Elastic Beanstalk environments?

Consider:

- Team ownership.
- Deployment independence.
- Scaling differences.
- Failure isolation.
- Data ownership.
- Release frequency.
- Organizational boundaries.

Do not create microservices solely to demonstrate architectural sophistication.

## Cost Architecture

### How would you optimize an Elastic Beanstalk architecture for cost?

Start with workload measurements.

Review:

- Instance sizing.
- Minimum capacity.
- Maximum capacity.
- Environment count.
- Load-balancer usage.
- Database capacity.
- Cache capacity.
- NAT traffic.
- Logging volume.
- Data transfer.

A cheaper architecture is not necessarily better if it creates:

- Higher failure probability.
- Longer recovery.
- Excessive operational work.
- Performance degradation.

Optimize total cost of ownership rather than one infrastructure component.

## Operational Architecture

### How would you prevent configuration drift?

Treat environment configuration as controlled infrastructure.

A desired workflow is:

```text
Configuration
      |
      v
Version Control
      |
      v
CI/CD
      |
      v
Environment
```

Manual production changes may occasionally be required during incidents, but they should subsequently be reconciled into the source-controlled configuration.

### How would you safely manage environment differences?

Separate environment-specific configuration from application code.

For example:

```text
Application Artifact
        |
        +------ Development Configuration
        |
        +------ Staging Configuration
        |
        +------ Production Configuration
```

Avoid creating separate application codebases for each environment.

Configuration should control environment behavior while the application artifact remains consistent.

## Platform Upgrade Strategy

### How would you architect a long-term Elastic Beanstalk platform upgrade process?

Treat runtime upgrades as continuous maintenance rather than emergency work.

A mature process is:

```text
Current Runtime
      |
      v
Compatibility Review
      |
      v
Dependency Updates
      |
      v
Automated Testing
      |
      v
Staging Upgrade
      |
      v
Production Validation
      |
      v
Controlled Rollout
```

For Python applications, validate:

- Python runtime.
- Django/FastAPI compatibility.
- Native dependencies.
- OpenSSL compatibility.
- Database drivers.
- WSGI/ASGI server behavior.
- Background workers.
- Monitoring agents.

### Why should runtime upgrades be separated from application feature releases?

Combining changes makes failure attribution difficult.

Suppose a release changes:

```text
Python Runtime
+
Django Version
+
Database Driver
+
Application Logic
```

and production fails.

The larger change surface makes root-cause analysis harder.

Smaller, independently validated changes improve operational safety.

## Migration Architecture

### How would you migrate a Django application from EC2 to Elastic Beanstalk?

Treat the migration as an architecture transition.

A reasonable sequence is:

```text
Existing EC2
    |
    v
Application Assessment
    |
    v
Externalize State
    |
    v
Build EB Environment
    |
    v
Deploy Application
    |
    v
Validate
    |
    v
Traffic Migration
    |
    v
Observe
    |
    v
Decommission Old Infrastructure
```

Before migration, identify:

- Local filesystem dependencies.
- Cron jobs.
- Background workers.
- Environment variables.
- IAM credentials.
- Database connections.
- Network dependencies.
- OS-level packages.
- Startup scripts.
- Monitoring agents.

### What is the most dangerous assumption during an EC2-to-Elastic-Beanstalk migration?

Assuming the existing server is the application.

It is often not.

The server may contain undocumented state such as:

- Local files.
- Manual configuration.
- Cron jobs.
- Installed packages.
- Environment variables.
- Cached data.
- Certificates.
- Operational scripts.

The migration should discover and explicitly model those dependencies.

## Architect-Level Scenario Questions

### Your Django API receives 10,000 requests per second. How would you evaluate whether Elastic Beanstalk is still appropriate?

Do not decide based solely on request count.

Analyze:

- Request complexity.
- CPU utilization.
- Memory usage.
- Request latency.
- Instance capacity.
- Database load.
- Cache hit rate.
- External dependency limits.
- Deployment requirements.
- Network throughput.
- Scaling speed.
- Operational requirements.

The question is whether Elastic Beanstalk can meet the required service-level objectives with acceptable cost and operational complexity.

### A business requires 99.99% availability. Is Elastic Beanstalk sufficient?

The service choice alone does not determine availability.

A 99.99% target requires approximately 52.56 minutes of downtime budget per year.

The architecture must consider:

- Application redundancy.
- Multi-AZ deployment.
- Database availability.
- Cache availability.
- Deployment strategy.
- Failure detection.
- Recovery automation.
- Dependency availability.
- Disaster recovery.

The correct answer is:

> Elastic Beanstalk can be part of a highly available architecture, but the availability target must be achieved by the complete system design.

### Your application must support a 10x traffic increase within five minutes. What would you evaluate?

Evaluate:

- Instance startup time.
- Auto Scaling responsiveness.
- Load-balancer capacity.
- Application initialization.
- Database capacity.
- Redis capacity.
- External API limits.
- Connection pools.
- Queue capacity.
- Cache warm-up.

A scaling policy is insufficient if the database takes several minutes to become the bottleneck.

### Your company wants Kubernetes because "Elastic Beanstalk is not enterprise-grade." How would you respond?

Challenge the premise.

Evaluate the actual requirements:

- Kubernetes-specific workloads.
- Platform standardization.
- Team expertise.
- Multi-service orchestration.
- Deployment requirements.
- Infrastructure customization.
- Compliance requirements.
- Operational model.

Elastic Beanstalk can support production workloads. Kubernetes may still be the better choice for a particular organization, but the decision should be requirement-driven rather than based on branding or perceived maturity.

## Architectural Anti-Patterns

### Treating Elastic Beanstalk as a database

Application instances should not be the authoritative storage layer for persistent business data.

### Storing uploads on local instance disks

Instance replacement can remove local files.

Use durable object storage for persistent uploads.

### Using one environment for every lifecycle stage

Production and non-production workloads should have appropriate isolation.

### Hardcoding credentials

Credentials in source control create security and rotation problems.

### Scaling only the web tier

The database, cache, queue, and external services must also support the resulting workload.

### Using sticky sessions to compensate for stateful application design

Externalize shared state instead.

### Deploying incompatible database migrations with rolling releases

Mixed-version deployments require schema compatibility.

### Relying only on CPU for scaling

CPU is not always the limiting resource.

Latency, queue depth, request count, memory, database load, and business metrics may be more useful signals.

### Treating successful deployment as successful release

A deployment can succeed while the application is functionally broken.

Use health checks, smoke tests, observability, and business-level validation.

## Architecture Decision Framework

When evaluating Elastic Beanstalk for a production system, consider the following dimensions:

| Dimension | Architectural Question |
|---|---|
| Compute | Does the workload fit the platform model? |
| Scaling | Can capacity increase at the required rate? |
| Availability | Can the required failure domains be isolated? |
| Database | Can the persistence layer meet the workload? |
| Networking | Can all dependencies communicate securely? |
| Security | Can least privilege be enforced? |
| Deployment | Can releases be performed safely? |
| Rollback | Can failures be reversed safely? |
| Observability | Can failures be detected and diagnosed? |
| Recovery | Can the system meet RTO/RPO? |
| Cost | Is the total operating cost acceptable? |
| Operations | Can the team operate the system reliably? |
| Evolution | Will the platform remain suitable as requirements change? |

## Key Takeaways

- Architect-level Elastic Beanstalk decisions should be requirement-driven rather than service-driven.
- Elastic Beanstalk is an application platform that abstracts infrastructure operations but does not remove architectural responsibility.
- High availability must be designed across the entire dependency graph, not just the application instances.
- Multi-AZ application instances are necessary for many production workloads but are not sufficient by themselves for end-to-end availability.
- Stateless application design is fundamental to reliable horizontal scaling.
- Persistent state should be externalized to durable and appropriately available services.
- Application scalability is limited by critical downstream dependencies such as PostgreSQL, Redis, queues, and external APIs.
- Auto Scaling configuration must be designed together with database capacity and connection management.
- More instances can increase load on shared dependencies and can therefore make a system less stable.
- Blue/green and immutable deployments reduce certain classes of deployment risk but do not solve database compatibility or business-logic failures.
- Database migrations should be designed independently from application deployment strategy.
- Expand-and-contract migrations are a useful pattern for maintaining compatibility across application versions.
- Security architecture should use private networking, security groups, least-privilege IAM, and managed secret storage.
- Health checks must reflect the application's actual ability to serve traffic without being so strict that transient dependency failures cause unnecessary instance replacement.
- Graceful degradation requires explicit classification of dependencies into critical and non-critical paths.
- Timeouts, bounded retries, backoff, jitter, and circuit breakers can prevent dependency failures from becoming cascading failures.
- Queues can absorb workload spikes and isolate slow processing, but they do not eliminate capacity constraints.
- Multi-region architecture should be justified by RTO/RPO and business requirements because it introduces substantial data and operational complexity.
- Active-active architectures generally require significantly more sophisticated data and consistency design than active-passive architectures.
- Runtime and platform upgrades should be treated as controlled production changes.
- Infrastructure migrations should uncover hidden server state rather than assuming that the existing machine fully represents the application.
- Microservices should be introduced for meaningful architectural reasons such as independent scaling, ownership, or deployment isolation rather than organizational fashion.
- Kubernetes should not automatically replace Elastic Beanstalk simply because it provides more infrastructure control.
- Cost optimization should consider total cost of ownership, operational effort, availability, and recovery requirements.
- Configuration should be reproducible and controlled to minimize drift.
- Disaster recovery requires tested restoration procedures, explicit RTO/RPO targets, and recoverable application and data state.
- Architect-level answers should explicitly discuss trade-offs, failure modes, blast radius, operational burden, and the conditions under which the chosen design should change.