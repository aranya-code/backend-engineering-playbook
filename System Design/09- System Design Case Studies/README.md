# README

## Overview

This directory contains production-oriented **System Design Case Studies** for studying how large-scale backend systems are decomposed, scaled, secured, and operated.

Each case study focuses on a recognizable real-world system and uses it to explore reusable distributed-systems patterns rather than attempting to reproduce the exact internal architecture of any specific company.

The case studies progressively cover problems such as:

- API design and request routing
- Data modeling
- Caching
- Database scaling
- Object storage
- Search
- Real-time communication
- Message queues and event streaming
- Asynchronous processing
- Feed generation
- Notifications
- Synchronization
- Distributed locking
- Rate limiting
- High availability
- Multi-region deployment
- Observability
- Disaster recovery
- Security and authorization
- Cost-aware architecture

The goal is to develop the ability to move from:

```text
Requirements
    ↓
Capacity estimation
    ↓
API design
    ↓
Data model
    ↓
High-level architecture
    ↓
Scaling strategy
    ↓
Reliability
    ↓
Security
    ↓
Observability
    ↓
Failure handling
```

Each case study should be treated as an architecture exercise rather than as a collection of company-specific facts.

## Case Studies

| File | Case Study | Primary Engineering Problems |
|---|---|---|
| [01- URL Shortener](./01-%20URL%20Shortener.md) | URL Shortener | ID generation, redirects, caching, analytics, high read throughput |
| [02- Rate Limiter](./02-%20Rate%20Limiter.md) | Rate Limiter | Distributed counters, Redis, algorithms, atomicity, consistency |
| [03- File Storage](./03-%20File%20Storage.md) | File Storage | Object storage, multipart uploads, metadata, CDN, durability |
| [04- Chat Application](./04-%20Chat%20Application.md) | Chat Application | WebSockets, message delivery, ordering, presence, offline users |
| [05- Notification System](./05-%20Notification%20System.md) | Notification System | Fan-out, queues, retries, preferences, delivery guarantees |
| [06- Search Autocomplete](./06-%20Search%20Autocomplete.md) | Search Autocomplete | Prefix search, indexing, caching, latency, ranking |
| [07- News Feed](./07-%20News%20Feed.md) | News Feed | Fan-out, ranking, caching, timelines, hot users |
| [08- YouTube](./08-%20YouTube.md) | YouTube | Video ingestion, transcoding, object storage, CDN, streaming |
| [09- Netflix](./09-%20Netflix.md) | Netflix | Video delivery, CDN, recommendation systems, resilience, multi-region architecture |
| [10- Uber](./10-%20Uber.md) | Uber | Geospatial indexing, real-time location, matching, trip state, event processing |
| [11- WhatsApp](./11-%20WhatsApp.md) | WhatsApp | Messaging, WebSockets, delivery states, presence, offline synchronization |
| [12- Twitter (X)](./12-%20Twitter%20(X).md) | Twitter (X) | Social graph, timelines, fan-out, ranking, high write/read throughput |
| [13- Instagram](./13-%20Instagram.md) | Instagram | Media storage, feeds, social graph, CDN, caching, fan-out |
| [14- Dropbox](./14-%20Dropbox.md) | Dropbox | File synchronization, versioning, metadata, offline clients, conflict resolution |
| [15- Google Drive](./15-%20Google%20Drive.md) | Google Drive | File storage, synchronization, sharing, permissions, search, versioning |

## How to Read the Case Studies

Do not memorize the architecture diagrams. Instead, use each case study to practice the reasoning process behind the architecture.

For every system, work through the following sequence:

```text
Functional Requirements
        ↓
Non-Functional Requirements
        ↓
Scale Estimation
        ↓
API Design
        ↓
Data Model
        ↓
Core Request Flow
        ↓
High-Level Architecture
        ↓
Bottleneck Identification
        ↓
Scaling Strategy
        ↓
Consistency Model
        ↓
Failure Handling
        ↓
Security
        ↓
Observability
        ↓
Disaster Recovery
```

The important question is not:

> "Which technology should I use?"

The better question is:

> "What workload or failure mode requires this technology?"

For example:

```text
High cache hit ratio
    → Redis

Large binary objects
    → Object Storage

Massive asynchronous workloads
    → Kafka / Queue

Long-running background processing
    → Celery / Workers

Low-latency service-to-service communication
    → gRPC

Public HTTP traffic
    → REST / HTTP

Global static or immutable content
    → CDN

Complex metadata queries
    → PostgreSQL / Distributed Database
```

Technology selection should follow system requirements rather than familiarity with a particular tool.

## Common Architecture Patterns

These case studies repeatedly use a small set of architectural patterns.

### Load Balancing

```text
                    Load Balancer
                         |
            +------------+------------+
            |            |            |
          API-1        API-2        API-3
```

Use load balancing to distribute traffic across stateless application instances and availability zones.

### Cache-Aside

```text
Client
  |
  v
API
  |
  v
Redis
  |
  +---- Hit ----> Response
  |
  +---- Miss
          |
          v
       Database
```

The cache should normally accelerate access to authoritative data rather than become the only copy of critical state.

### Asynchronous Processing

```text
API
 |
 v
Database
 |
 v
Event / Queue
 |
 +--> Worker A
 +--> Worker B
 +--> Worker C
```

Move expensive or non-critical work away from synchronous request paths.

### Event-Driven Architecture

```text
Producer
   |
   v
Kafka
   |
   +--> Consumer A
   +--> Consumer B
   +--> Consumer C
```

This allows independent consumers to process the same event stream for different purposes.

### Object Storage

```text
Client
  |
  v
API
  |
  +--> Authorization
  |
  v
Signed URL
  |
  v
Object Storage
  |
  v
CDN
```

Large binary transfers should generally bypass application servers.

### Database Replication

```text
                Primary
               /       \
              v         v
         Replica-1   Replica-2
```

Replication improves read scalability and availability, but introduces replication lag and does not automatically solve write scalability.

### Sharding

```text
                 Router
                   |
        +----------+----------+
        |          |          |
      Shard A    Shard B    Shard C
```

Sharding distributes data and workload across independent partitions when a single database cannot meet scale requirements.

## System Design Decision Framework

When evaluating an architecture, consider these dimensions:

| Dimension | Questions |
|---|---|
| Traffic | How many requests per second? |
| Data | How much data is stored and generated? |
| Read/write ratio | Is the workload read-heavy or write-heavy? |
| Latency | What are p50, p95, and p99 requirements? |
| Consistency | Which operations require strong consistency? |
| Availability | What downtime is acceptable? |
| Durability | How much data loss is acceptable? |
| Scalability | Which component becomes the first bottleneck? |
| Security | What must be protected and from whom? |
| Cost | Which resources dominate infrastructure cost? |
| Operations | How difficult is the system to deploy and operate? |
| Recovery | What are the RPO and RTO requirements? |

A strong architecture explicitly identifies trade-offs.

## Capacity Estimation

Before selecting infrastructure, estimate the workload.

For example:

```text
100 million users
10% daily active users
10 million DAU
10 requests/user/day

Requests/day
= 10M × 10
= 100M requests/day

Average RPS
≈ 100M / 86,400
≈ 1,157 RPS
```

Average traffic is not enough.

If peak traffic is 10× average:

```text
Peak RPS
≈ 11,570 RPS
```

Similar calculations should be performed for:

- Storage.
- Bandwidth.
- Database writes.
- Database reads.
- Cache operations.
- Queue throughput.
- Object-storage operations.

Use assumptions explicitly. The goal is to determine the order of magnitude rather than obtain false precision.

## Data Modeling

A recurring principle across these case studies is to separate:

```text
Authoritative State
```

from:

```text
Derived State
```

### Authoritative State

Examples:

- Users.
- Orders.
- Messages.
- Files.
- Permissions.
- Payments.
- Current versions.

### Derived State

Examples:

- Search indexes.
- Caches.
- Recommendation results.
- Thumbnails.
- Analytics aggregates.
- Notification queues.

Derived state should generally be rebuildable.

This distinction makes failure recovery much easier.

## Consistency

Not every operation requires the same consistency model.

| Workload | Typical Consistency |
|---|---|
| Payment state | Strong |
| Authorization | Strong |
| Account ownership | Strong |
| Inventory | Strong |
| Chat delivery state | Carefully ordered / application-defined |
| Search | Eventual |
| Feed ranking | Eventual |
| Analytics | Eventual |
| Recommendations | Eventual |
| Thumbnails | Eventual |
| Notifications | Eventual |

A senior-level design does not simply choose "strong consistency" or "eventual consistency" for the entire system.

Consistency should be selected per data path.

## Reliability Patterns

Common reliability patterns appearing across the case studies include:

- Timeouts.
- Retries with exponential backoff.
- Jitter.
- Circuit breakers.
- Bulkheads.
- Idempotency keys.
- Transactional outbox.
- Dead-letter queues.
- Consumer idempotency.
- Health checks.
- Graceful degradation.
- Backpressure.
- Rate limiting.
- Replication.
- Multi-AZ deployment.
- Automated failover.
- Reconciliation jobs.

### Idempotency

Distributed systems frequently retry operations.

A request may therefore arrive more than once:

```text
request A
request A
```

Critical operations should be designed so that repeated execution does not produce unintended side effects.

For example:

```http
POST /payments
Idempotency-Key: 8b6d...
```

The server can associate the key with the operation result.

### Transactional Outbox

When database state and events must remain consistent:

```text
Database Transaction
    |
    +--> Business State
    |
    +--> Outbox Event
```

A publisher then sends the outbox event to Kafka or another messaging system.

This avoids the classic failure:

```text
Database commit succeeds
Kafka publish fails
```

## Scalability Patterns

### Vertical Scaling

Increase:

```text
CPU
RAM
Disk
Network
```

Useful as a short-term strategy but has physical and economic limits.

### Horizontal Scaling

Add instances:

```text
API-1
API-2
API-3
...
API-N
```

Works best when services are stateless.

### Read Replicas

Useful for read-heavy database workloads.

### Partitioning

Split data by:

```text
tenant
user
time
region
hash
```

### Sharding

Distribute partitions across independent database nodes.

### Caching

Reduce repeated database work.

### Asynchronous Processing

Move expensive work away from request paths.

## Messaging and Event Streaming

Use a queue when the primary requirement is:

```text
work distribution
```

Use an event stream when the requirement includes:

```text
durability
multiple consumers
replay
high throughput
ordered partitions
```

| Requirement | Typical Choice |
|---|---|
| Background task | Celery |
| Simple work queue | Queue |
| Durable event stream | Kafka |
| Pub/sub notification | SNS-like system |
| Scheduled work | Scheduler + worker |
| Service-to-service synchronous call | REST / gRPC |

The exact choice depends on throughput, delivery semantics, ordering, replay requirements, and operational constraints.

## Caching Strategy

Common cacheable data includes:

- User profiles.
- Hot objects.
- Feed pages.
- Search suggestions.
- Session data.
- Permission results.
- Rate-limit counters.
- Frequently accessed metadata.

Avoid caching blindly.

For every cache, define:

```text
What is cached?
Why is it cached?
TTL?
Invalidation strategy?
Maximum size?
Failure behavior?
Consistency requirements?
```

A cache without an invalidation strategy is often a future correctness problem.

## API Design

Public APIs should have:

- Clear resource boundaries.
- Authentication.
- Authorization.
- Validation.
- Pagination.
- Rate limiting.
- Stable identifiers.
- Versioning strategy.
- Consistent error responses.
- Idempotency where appropriate.

Example:

```http
GET /v1/files/{file_id}
GET /v1/files/{file_id}/versions
POST /v1/files
PATCH /v1/files/{file_id}
DELETE /v1/files/{file_id}
```

For internal high-throughput communication:

```text
Service A
   |
   v
gRPC
   |
   v
Service B
```

Choose REST or gRPC based on the communication requirements rather than using one protocol universally.

## Pagination

Offset pagination:

```http
GET /items?page=10&limit=50
```

is simple but becomes expensive and unstable for frequently changing datasets.

Cursor pagination:

```http
GET /items?cursor=eyJpZCI6...
```

is usually preferable for:

- Feeds.
- Messages.
- Event streams.
- Synchronization.
- Large changing datasets.

Stable ordering is essential.

## Security Principles

Every case study should consider:

```text
Authentication
Authorization
Encryption
Secrets
Input validation
Rate limiting
Abuse prevention
Audit logging
Data isolation
Credential rotation
```

Common security mistakes include:

- Trusting client-provided permissions.
- Exposing internal IDs unnecessarily.
- Long-lived signed URLs.
- Missing rate limits.
- Logging secrets.
- Treating uploaded files as trusted.
- Using predictable tokens.
- Relying solely on frontend authorization.
- Missing tenant isolation.

Security should be part of the architecture rather than added after implementation.

## Observability

A production architecture needs visibility into:

```text
Logs
Metrics
Traces
Alerts
```

Important golden signals:

| Signal | Example |
|---|---|
| Latency | API p95/p99 |
| Traffic | Requests/sec |
| Errors | 5xx rate |
| Saturation | CPU, memory, DB connections |
| Queue lag | Kafka consumer lag |
| Cache | Hit/miss ratio |
| Database | Query latency, locks |
| Storage | Growth and error rate |

Distributed tracing becomes especially valuable when a request crosses:

```text
Nginx
→ API
→ Redis
→ PostgreSQL
→ Kafka
→ Worker
→ Object Storage
```

## Failure-Oriented Thinking

A strong system-design answer should always ask:

```text
What happens if this component fails?
```

For every major dependency, identify:

| Dependency | Failure Strategy |
|---|---|
| Redis | Fallback / degraded mode |
| PostgreSQL | Replica / failover |
| Kafka | Retry / durable backlog |
| Object Storage | Retry / pending state |
| Search | Serve stale or unavailable search |
| Worker | Retry / DLQ |
| Notification service | Cursor-based recovery |
| CDN | Origin fallback where appropriate |

The architecture should degrade gracefully instead of turning every dependency failure into a total outage.

## Case Study Progression

The case studies can be viewed as a progression of increasingly complex distributed-system problems:

```text
URL Shortener
      ↓
Rate Limiter
      ↓
File Storage
      ↓
Chat
      ↓
Notifications
      ↓
Search
      ↓
News Feed
      ↓
Video Platforms
      ↓
Real-Time Location
      ↓
Social Networks
      ↓
Distributed File Synchronization
```

The later systems intentionally combine patterns introduced by the earlier ones.

For example:

```text
Instagram
   |
   +--> Object Storage
   +--> CDN
   +--> News Feed
   +--> Social Graph
   +--> Caching

Dropbox
   |
   +--> Object Storage
   +--> Metadata
   +--> Synchronization
   +--> Versioning
   +--> Offline Clients

Google Drive
   |
   +--> Object Storage
   +--> Synchronization
   +--> Versioning
   +--> Permissions
   +--> Search
   +--> Event Processing
```

## Technology Mapping

These case studies can be implemented or prototyped using technologies commonly used in modern backend systems.

| Concern | Technologies |
|---|---|
| API | Django REST Framework, FastAPI |
| Internal RPC | gRPC |
| Reverse proxy | Nginx |
| Database | PostgreSQL |
| Cache | Redis |
| Event streaming | Kafka |
| Background jobs | Celery |
| Containers | Docker |
| Orchestration | Kubernetes |
| Object storage | Amazon S3 |
| CDN | Amazon CloudFront |
| Compute | AWS ECS / EKS / EC2 |
| Monitoring | CloudWatch, Prometheus, Grafana |
| CI/CD | GitHub Actions |
| Search | OpenSearch / Elasticsearch |

Technology selection should remain workload-driven.

## Recommended Architecture Review Checklist

Before considering a system-design case study complete, verify:

### Requirements

- [ ] Functional requirements identified.
- [ ] Non-functional requirements identified.
- [ ] Latency targets defined.
- [ ] Availability target defined.
- [ ] Data durability requirements defined.

### Capacity

- [ ] Peak RPS estimated.
- [ ] Read/write ratio estimated.
- [ ] Storage growth estimated.
- [ ] Bandwidth estimated.
- [ ] Queue throughput estimated.

### Architecture

- [ ] API layer defined.
- [ ] Data stores selected.
- [ ] Cache strategy defined.
- [ ] Async processing identified.
- [ ] Service boundaries justified.
- [ ] Object storage considered for large binaries.

### Data

- [ ] Data model defined.
- [ ] Indexes identified.
- [ ] Partitioning strategy considered.
- [ ] Consistency requirements documented.
- [ ] Retention policy defined.

### Reliability

- [ ] Timeouts defined.
- [ ] Retry strategy defined.
- [ ] Idempotency considered.
- [ ] Failure scenarios documented.
- [ ] Backpressure considered.
- [ ] Disaster recovery defined.

### Security

- [ ] Authentication defined.
- [ ] Authorization defined.
- [ ] Encryption considered.
- [ ] Rate limiting considered.
- [ ] Secrets management defined.
- [ ] Audit logging considered.

### Operations

- [ ] Metrics defined.
- [ ] Logs defined.
- [ ] Distributed tracing considered.
- [ ] Alerts defined.
- [ ] Capacity monitoring defined.
- [ ] Deployment strategy defined.

## Interview Approach

For a system-design interview, avoid immediately drawing a complex architecture.

A strong sequence is:

```text
Clarify Requirements
        ↓
Estimate Scale
        ↓
Define APIs
        ↓
Model Data
        ↓
Draw Core Architecture
        ↓
Identify Bottlenecks
        ↓
Scale Critical Components
        ↓
Discuss Consistency
        ↓
Discuss Reliability
        ↓
Discuss Security
        ↓
Discuss Trade-offs
```

The interviewer is generally evaluating engineering reasoning, not the number of boxes on the diagram.

When presenting a component, explain:

```text
Why is it needed?
What workload does it handle?
Why this technology?
What happens when it fails?
How does it scale?
What consistency does it provide?
What does it cost?
```

## Common Interview Mistakes

### Starting With Technology

Weak:

```text
Let's use Kafka, Redis, Kubernetes, and Cassandra.
```

Better:

```text
The system has a high-volume asynchronous workload
with multiple independent consumers, so a durable event
stream is appropriate.
```

### Ignoring Scale

A design that works for:

```text
1,000 users
```

may fail completely at:

```text
100 million users
```

### Ignoring Failure Modes

Every major dependency should have an explicit failure strategy.

### Overusing Microservices

A modular monolith can be a better starting point when:

- Team size is small.
- Traffic is moderate.
- Boundaries are not yet understood.
- Independent scaling is unnecessary.

### Treating Kafka as a Database

Kafka is an event-streaming platform, not a replacement for every transactional data store.

### Treating Redis as a Database

Redis is excellent for caching and specific high-speed data structures, but critical authoritative state requires deliberate durability and recovery guarantees.

### Assuming More Replicas Solve Everything

Replication does not automatically solve:

- Hot partitions.
- Lock contention.
- Poor indexes.
- Network bottlenecks.
- Hot keys.
- Application-level contention.

## Navigation

### Foundation Case Studies

- [01- URL Shortener](./01-%20URL%20Shortener.md)
- [02- Rate Limiter](./02-%20Rate%20Limiter.md)
- [03- File Storage](./03-%20File%20Storage.md)

### Communication and Event-Driven Systems

- [04- Chat Application](./04-%20Chat%20Application.md)
- [05- Notification System](./05-%20Notification%20System.md)

### Search and Feed Systems

- [06- Search Autocomplete](./06-%20Search%20Autocomplete.md)
- [07- News Feed](./07-%20News%20Feed.md)

### Large-Scale Media Platforms

- [08- YouTube](./08-%20YouTube.md)
- [09- Netflix](./09-%20Netflix.md)

### Real-Time and Social Platforms

- [10- Uber](./10-%20Uber.md)
- [11- WhatsApp](./11-%20WhatsApp.md)
- [12- Twitter (X)](./12-%20Twitter%20(X).md)
- [13- Instagram](./13-%20Instagram.md)

### Distributed File Systems

- [14- Dropbox](./14-%20Dropbox.md)
- [15- Google Drive](./15-%20Google%20Drive.md)

## Key Takeaways

- **System design should start with requirements, scale, consistency, and failure modes rather than technology selection.**
- **Separate authoritative state from derived state so caches, indexes, previews, and analytics can fail or be rebuilt independently.**
- **Use the appropriate scaling pattern—caching, replication, partitioning, sharding, asynchronous processing, or object storage—based on the actual bottleneck.**
- **Production architecture must explicitly address security, reliability, observability, disaster recovery, and operational cost.**
- **The strongest interview answers explain architectural trade-offs and failure behavior rather than simply presenting a collection of technologies.**