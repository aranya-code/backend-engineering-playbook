# README

## Overview

The **Backend Python** section focuses on applying Python to production backend systems rather than treating Python as an isolated programming language.

The preceding sections establish Python fundamentals, object-oriented design, concurrency, memory management, and performance. This section builds on those concepts and applies them to systems that serve requests, access databases, communicate with other services, process asynchronous work, and operate continuously in production.

The central engineering model is:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI / Django
  ↓
Application / Service Layer
  ↓
Repositories / Infrastructure
  ├── PostgreSQL
  ├── Redis
  ├── External APIs
  └── Kafka
        ↓
   Celery / Workers
```

The section emphasizes:

- maintainable Python project architecture;
- reproducible environments and dependency management;
- configuration and secrets;
- HTTP and API design;
- authentication and authorization;
- request validation;
- database access and transaction boundaries;
- connection pooling;
- caching;
- message queues and background jobs;
- webhooks and CLI applications;
- dependency injection and service-layer design;
- observability;
- health checks;
- graceful shutdown;
- reliability, scalability, security, and operational behavior.

---

## Section Structure

| File | Topic | Primary Focus |
|---|---|---|
| `01- Python Project Structure.md` | Python Project Structure | Organizing production Python applications |
| `02- Virtual Environments.md` | Virtual Environments | Environment isolation and reproducibility |
| `03- Dependency Management.md` | Dependency Management | Dependency graphs, versions, locks, and upgrades |
| `04- pyproject.toml.md` | pyproject.toml | Modern Python project configuration |
| `05- Package Management.md` | Package Management | Installing, building, publishing, and inspecting packages |
| `06- Environment Configuration.md` | Environment Configuration | Runtime configuration and environment-specific settings |
| `07- Configuration Management.md` | Configuration Management | Configuration ownership, validation, layering, and lifecycle |
| `08- Logging.md` | Logging | Python logging fundamentals and operational logging |
| `09- Structured Logging.md` | Structured Logging | Machine-readable logs, context, correlation, and event schemas |
| `10- HTTP Fundamentals.md` | HTTP Fundamentals | HTTP semantics, lifecycle, headers, methods, and protocols |
| `11- HTTP Clients.md` | HTTP Clients | Reliable outbound HTTP communication |
| `12- REST API Design.md` | REST API Design | Resource-oriented API contracts and operational behavior |
| `13- API Clients.md` | API Clients | Typed and reliable integrations with external/internal APIs |
| `14- Request Validation.md` | Request Validation | Validating untrusted HTTP input and enforcing boundaries |
| `15- Authentication and Authorization.md` | Authentication and Authorization | Identity, credentials, tokens, sessions, and access control |
| `16- Database Connectivity.md` | Database Connectivity | Python database drivers, sessions, connections, and lifecycle |
| `17- SQL Integration.md` | SQL Integration | SQL, ORMs, repositories, queries, indexes, and database integration |
| `18- Connection Pooling.md` | Connection Pooling | Reusing database connections and controlling database concurrency |
| `19- Transactions.md` | Transactions | ACID, isolation, locking, consistency, and transaction boundaries |
| `20- Caching.md` | Caching | Cache strategies, invalidation, consistency, and Redis |
| `21- Message Queues.md` | Message Queues | Asynchronous messaging, delivery guarantees, retries, and backpressure |
| `22- Background Jobs.md` | Background Jobs | Reliable asynchronous application work and worker systems |
| `23- Webhooks.md` | Webhooks | Event delivery, signatures, retries, deduplication, and processing |
| `24- CLI Applications.md` | CLI Applications | Production command-line interfaces and operational tooling |
| `25- Dependency Injection.md` | Dependency Injection | Explicit dependency ownership, composition, and testability |
| `26- Service Layer.md` | Service Layer | Application use cases, orchestration, and business workflows |
| `27- Repository Pattern.md` | Repository Pattern | Persistence abstraction and application/database boundaries |
| `28- Secrets Management.md` | Secrets Management | Secure storage, retrieval, rotation, and usage of credentials |
| `29- Observability.md` | Observability | Logs, metrics, traces, correlation, and system diagnosis |
| `30- Health Checks.md` | Health Checks | Liveness, readiness, startup, dependency health, and orchestration |
| `31- Graceful Shutdown.md` | Graceful Shutdown | Draining traffic, terminating work, and releasing resources safely |

---

## Backend Python Mental Model

A production Python backend should be understood as a set of boundaries rather than as a collection of framework modules.

```text
                    ┌──────────────────────┐
                    │       Client         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ HTTP / gRPC Boundary │
                    │ Auth / Validation    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Application Layer  │
                    │   Service / Use Case │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │ Repository │ │   Domain   │ │  Gateway   │
          │            │ │   Logic    │ │ External   │
          └─────┬──────┘ └────────────┘ └─────┬──────┘
                │                             │
                ▼                             ▼
          ┌────────────┐               ┌────────────┐
          │ PostgreSQL │               │ HTTP / API │
          └────────────┘               └────────────┘
```

The objective is not to maximize the number of layers.

The objective is to establish clear ownership:

| Responsibility | Typical owner |
|---|---|
| HTTP parsing | Framework/server |
| Request validation | API/schema boundary |
| Authentication | Authentication layer |
| Authorization | Application/domain policy |
| Business workflow | Service/application layer |
| Domain invariants | Domain model |
| Persistence | Repository/data-access layer |
| External integration | Infrastructure adapter |
| Transactions | Unit of Work/service boundary |
| Configuration | Configuration layer |
| Logging | Logging infrastructure |
| Metrics/tracing | Observability infrastructure |
| Process lifecycle | Application/server runtime |

---

## Project Architecture

A production-oriented Python application commonly separates transport, application logic, domain behavior, and infrastructure.

```text
src/
└── app/
    ├── api/
    │   ├── routes/
    │   ├── schemas/
    │   └── dependencies.py
    ├── application/
    │   ├── services/
    │   └── commands/
    ├── domain/
    │   ├── models/
    │   ├── value_objects/
    │   └── policies/
    ├── infrastructure/
    │   ├── database/
    │   ├── repositories/
    │   ├── clients/
    │   ├── messaging/
    │   └── cache/
    ├── config/
    ├── observability/
    └── main.py
```

The exact structure should follow application complexity.

A small service does not need every possible abstraction.

A large service benefits from explicit boundaries because otherwise business logic tends to spread across:

- route handlers;
- ORM models;
- serializers;
- Celery tasks;
- CLI commands;
- webhook handlers.

---

## Application Lifecycle

Backend applications have more than a request lifecycle.

The full lifecycle is:

```text
Process starts
     ↓
Load configuration
     ↓
Initialize logging
     ↓
Initialize telemetry
     ↓
Initialize connection pools/clients
     ↓
Startup checks
     ↓
Ready
     ↓
Serve traffic
     ↓
Process background work
     ↓
Readiness becomes false
     ↓
Drain active work
     ↓
Close resources
     ↓
Exit
```

This lifecycle connects:

- configuration;
- health checks;
- observability;
- dependency management;
- connection pooling;
- background jobs;
- graceful shutdown.

---

## Configuration and Secrets

Configuration controls application behavior.

Examples include:

```text
DATABASE_URL
REDIS_URL
KAFKA_BROKERS
LOG_LEVEL
REQUEST_TIMEOUT_SECONDS
FEATURE_FLAG
```

Secrets are a special class of configuration and require stronger handling:

```text
database password
API token
OAuth client secret
private key
signing secret
```

A production application should retrieve secrets from an appropriate secret-management system rather than storing them in source code or Git.

Common sources include:

- AWS Secrets Manager;
- AWS Systems Manager Parameter Store;
- Kubernetes Secrets;
- dedicated secret-management platforms.

Environment variables can provide runtime configuration, but they should not be treated as a complete secrets-management strategy.

---

## Dependency Management

Python dependency management has several separate concerns:

```text
pyproject.toml
      ↓
dependency declarations
      ↓
resolver
      ↓
lock/sync mechanism
      ↓
environment
      ↓
build artifact
```

Production systems should have a reproducible dependency workflow.

Important practices include:

- define direct dependencies explicitly;
- constrain versions deliberately;
- maintain lock information where appropriate;
- update dependencies systematically;
- scan for vulnerabilities;
- avoid dependency confusion;
- build immutable deployment artifacts.

---

## HTTP Backend Flow

A typical request travels through several boundaries:

```text
Client
 ↓
DNS
 ↓
Load Balancer
 ↓
Nginx / Proxy
 ↓
ASGI/WSGI Server
 ↓
FastAPI / Django
 ↓
Authentication
 ↓
Validation
 ↓
Service Layer
 ↓
Repository / Client
 ↓
Database / External Service
 ↓
Response
```

Each layer has different responsibilities.

For example:

```text
HTTP layer
→ transport semantics

Validation
→ input shape and constraints

Authentication
→ who is calling?

Authorization
→ what may they do?

Service
→ what operation should happen?

Repository
→ how is state persisted?

Database
→ what durable invariants must hold?
```

---

## Database Architecture

Python database access commonly follows:

```text
FastAPI / Django
      ↓
Service
      ↓
Repository / ORM
      ↓
Connection Pool
      ↓
PostgreSQL
```

The connection pool is a concurrency boundary.

If there are:

```text
5 Kubernetes pods
× 4 worker processes
× 10 pool connections
```

the application can potentially demand approximately:

```text
200 database connections
```

before considering overflow or other clients.

Therefore database capacity must be planned across the entire deployment, not per process in isolation.

---

## Transaction Boundaries

Transactions should correspond to meaningful consistency boundaries.

Typical flow:

```text
HTTP request
     ↓
Service
     ↓
BEGIN
     ↓
Read/write database state
     ↓
Validate invariants
     ↓
COMMIT
     ↓
Return result
```

Avoid keeping a transaction open while performing unrelated slow work such as:

- external HTTP calls;
- long computations;
- sleeps;
- user interaction.

When database changes and asynchronous events must remain consistent, patterns such as the transactional outbox can be appropriate:

```text
Transaction
 ├── update business state
 └── insert outbox event
          ↓
       COMMIT
          ↓
   publisher/worker
          ↓
        Kafka
```

---

## Repository Pattern

The repository pattern provides an application-facing persistence boundary.

```text
Service
  ↓
Repository interface
  ↓
PostgreSQL implementation
```

A repository should encapsulate persistence concerns rather than becoming a second business-logic layer.

For example:

```python
from typing import Protocol


class UserRepository(Protocol):
    async def get_by_id(self, user_id: str) -> "User | None":
        ...

    async def save(self, user: "User") -> None:
        ...
```

The service can depend on the interface:

```text
Application
    ↓
UserRepository
    ↓
PostgreSQLRepository
```

Repositories are most valuable when they clarify boundaries and allow persistence concerns to remain isolated.

They are not automatically beneficial for every simple CRUD endpoint.

---

## Service Layer

The service layer represents application-level use cases.

For example:

```text
CreateOrderService
     ↓
Validate operation
     ↓
Authorize action
     ↓
Load customer
     ↓
Create order
     ↓
Persist order
     ↓
Publish event
     ↓
Return result
```

The service coordinates the workflow.

A useful responsibility split is:

```text
Controller
→ transport

Service
→ use case / workflow

Domain
→ business invariants

Repository
→ persistence

Gateway
→ external systems
```

This makes the same use case reusable from:

- REST;
- gRPC;
- CLI;
- Celery;
- webhooks;
- Kafka consumers.

---

## Dependency Injection

Dependency injection makes dependencies explicit.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        payment_client: PaymentClient,
    ) -> None:
        self.repository = repository
        self.payment_client = payment_client
```

The application composition root decides which implementations are used.

This improves:

- testability;
- ownership;
- configurability;
- dependency visibility.

FastAPI provides a dependency system, but dependency injection is an architectural technique rather than a framework-specific feature.

Avoid injecting every object merely for the sake of abstraction.

---

## Authentication and Authorization

Authentication answers:

> Who is the caller?

Authorization answers:

> What is the caller allowed to do?

Typical backend flow:

```text
Request
 ↓
Authenticate credentials/token
 ↓
Resolve identity
 ↓
Authorize operation
 ↓
Execute service
```

Common mechanisms include:

- sessions and cookies;
- API keys;
- OAuth 2.0;
- OpenID Connect;
- access tokens;
- service-to-service credentials.

Authorization may use:

- RBAC;
- ABAC;
- resource ownership;
- policy engines;
- explicit domain rules.

Authentication does not imply authorization.

---

## Request Validation

All external input should be treated as untrusted.

Validation typically occurs at multiple levels:

```text
HTTP input
 ↓
Schema validation
 ↓
Application validation
 ↓
Domain validation
 ↓
Database constraints
```

These layers solve different problems.

For example:

```text
schema:
email must be syntactically valid

application:
customer must be active

domain:
order cannot transition from CANCELLED to PAID

database:
order ID must be unique
```

Database constraints remain essential because application-level validation alone cannot eliminate concurrent race conditions.

---

## Caching

Caching reduces repeated expensive work.

Typical flow:

```text
Request
 ↓
Check cache
 ├── hit → return
 │
 └── miss
       ↓
    Database
       ↓
    Populate cache
       ↓
    Return
```

Redis is commonly used for distributed caching.

Important cache concerns include:

- key design;
- TTL;
- invalidation;
- stale data;
- stampedes;
- hot keys;
- memory limits;
- eviction;
- serialization;
- consistency.

Caching should be treated as a performance optimization with explicit correctness requirements, not as a replacement for durable storage.

---

## Message Queues

Queues separate request handling from asynchronous processing.

```text
API
 ↓
Publish job
 ↓
Queue
 ↓
Worker
 ↓
Database / External API
```

This is useful when work:

- takes too long for an HTTP request;
- can be retried;
- should absorb traffic bursts;
- needs independent worker scaling.

Important delivery concepts include:

- at-most-once;
- at-least-once;
- duplicate delivery;
- acknowledgments;
- retries;
- dead-letter queues;
- ordering;
- backpressure.

Production consumers should generally be idempotent.

---

## Background Jobs

Background jobs move work outside the synchronous request path.

Example:

```text
POST /reports
     ↓
Create job
     ↓
Return 202 + job ID
     ↓
Queue
     ↓
Celery worker
     ↓
Generate report
     ↓
Store result
```

Job systems should define:

- job state;
- retries;
- timeouts;
- idempotency;
- cancellation;
- progress;
- failure handling;
- observability;
- persistence.

A background job is not inherently reliable merely because it runs outside the HTTP request.

---

## Webhooks

Webhooks are HTTP-based event delivery mechanisms.

Inbound webhook flow:

```text
External Provider
       ↓
Webhook Endpoint
       ↓
Verify Signature
       ↓
Validate Payload
       ↓
Deduplicate Event
       ↓
Persist Event
       ↓
Queue Processing
       ↓
Return 2xx
```

The endpoint should usually acknowledge quickly and process substantial work asynchronously.

Production webhook systems must handle:

- duplicate delivery;
- retries;
- replay attacks;
- signature validation;
- timestamp validation;
- ordering;
- provider outages;
- malformed payloads;
- schema evolution.

---

## CLI Applications

Backend systems often need operational CLIs for:

- migrations;
- data repair;
- administrative workflows;
- backfills;
- cache management;
- diagnostics;
- batch processing.

A CLI should reuse application services rather than duplicating business logic.

```text
CLI
 ↓
Application Service
 ↓
Repository / Infrastructure
```

The CLI should also have explicit:

- exit codes;
- input validation;
- logging;
- configuration;
- timeout behavior;
- idempotency;
- signal handling.

---

## Observability

Production systems must expose enough information to answer:

```text
Is the system healthy?
What is slow?
What is failing?
Where is the failure?
Who is affected?
When did it begin?
What changed?
```

The three primary observability signals are:

| Signal | Best for |
|---|---|
| Logs | Detailed events and diagnostic context |
| Metrics | Aggregation, alerting, trends, SLOs |
| Traces | Distributed request flow and latency attribution |

Correlation identifiers connect these signals:

```text
Request
 ├── request_id
 ├── trace_id
 └── user/tenant context where appropriate
       ↓
Service
       ↓
Database / Redis / Kafka / HTTP
```

Structured logging and distributed tracing should be designed together.

---

## Health Checks

Health endpoints answer operational questions.

A useful distinction is:

| Check | Purpose |
|---|---|
| Startup | Has initialization completed? |
| Liveness | Is the process/runtime functioning? |
| Readiness | Should traffic be routed here? |

A database outage does not necessarily mean the process is dead.

Therefore, liveness and readiness should not automatically have identical dependency checks.

For Kubernetes:

```text
startupProbe
     ↓
livenessProbe
     ↓
readinessProbe
```

Readiness is particularly important during deployments and graceful shutdown.

---

## Graceful Shutdown

A production service should shut down predictably.

Typical sequence:

```text
SIGTERM
  ↓
Mark not ready
  ↓
Stop accepting new work
  ↓
Drain in-flight requests
  ↓
Stop consumers/background work
  ↓
Finish or cancel owned tasks
  ↓
Commit/rollback active operations
  ↓
Close pools and clients
  ↓
Flush bounded telemetry
  ↓
Exit
```

Shutdown must have a deadline.

A service that waits forever for one stuck request is not gracefully shutting down.

Critical state should remain recoverable even when shutdown becomes abrupt because `SIGKILL`, crashes, OOM termination, and node failures bypass application cleanup.

---

## Security Boundaries

Backend Python security is distributed across multiple layers.

```text
Internet
  ↓
TLS
  ↓
Reverse Proxy
  ↓
Authentication
  ↓
Authorization
  ↓
Input Validation
  ↓
Application Logic
  ↓
Database
```

Important concerns include:

- TLS;
- authentication;
- authorization;
- secret management;
- SQL injection prevention;
- SSRF protection;
- request-size limits;
- rate limiting;
- secure serialization;
- dependency security;
- sensitive-data handling;
- audit logging.

Never assume framework defaults completely define the application's security boundary.

---

## Performance Model

Backend performance is multi-dimensional.

```text
Request latency
 = network
 + application CPU
 + database
 + cache
 + external services
 + serialization
 + queueing
```

Use the appropriate tool for the question:

| Question | Tool |
|---|---|
| Algorithmic growth | Complexity analysis |
| Python CPU hotspot | `cProfile` / sampling profiler |
| Small implementation comparison | `timeit` |
| Python memory allocations | `tracemalloc` |
| Database query performance | `EXPLAIN ANALYZE` |
| End-to-end request latency | Distributed tracing |
| Production throughput | Load testing / metrics |

Do not optimize based solely on intuition.

---

## Concurrency and Capacity

Concurrency must be considered across the whole system.

```text
Kubernetes replicas
 ×
worker processes
 ×
thread/task concurrency
 ×
connection pools
```

Increasing application concurrency can increase pressure on:

- PostgreSQL;
- Redis;
- external APIs;
- Kafka;
- CPU;
- memory.

More workers do not automatically produce more throughput.

The bottleneck may simply move downstream.

---

## Memory Management

Python backend processes can consume memory through:

- object graphs;
- request bodies;
- ORM result sets;
- caches;
- connection pools;
- async tasks;
- queues;
- serialization buffers;
- worker processes.

Large workloads should use:

- streaming;
- batching;
- pagination;
- bounded queues;
- generators;
- selective column retrieval;
- explicit cache limits.

Monitor both application-level allocations and process RSS.

---

## Testing Backend Python

Testing should reflect architectural boundaries.

A practical strategy is:

```text
Unit tests
   ↓
Service/domain behavior
   ↓
Integration tests
   ↓
PostgreSQL / Redis / Kafka
   ↓
API tests
   ↓
Contract / end-to-end tests
```

Use mocks selectively.

Good candidates for fakes/mocks:

- external payment providers;
- third-party APIs;
- time;
- random identifiers;
- expensive infrastructure.

Prefer real infrastructure integration tests for critical database behavior.

---

## CI/CD

A production Python CI pipeline commonly includes:

```text
Commit
  ↓
Lint / Format
  ↓
Type Check
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Security / Dependency Checks
  ↓
Build Wheel / Container
  ↓
Publish Artifact
  ↓
Deploy
  ↓
Health Verification
```

The deployment artifact should be immutable.

Avoid rebuilding dependencies differently between testing and production.

---

## Docker

A Python container should normally contain:

- application code;
- runtime;
- resolved dependencies;
- required system libraries;
- configuration interface.

A typical deployment is:

```text
Docker Image
    ↓
Kubernetes Pod
    ↓
Python Worker
    ↓
FastAPI / Django
```

The container should not contain environment-specific secrets baked into the image.

Build-time configuration and runtime configuration should remain separate.

---

## Kubernetes

Kubernetes introduces operational dimensions that application code must respect.

Important concepts include:

- readiness;
- liveness;
- startup;
- resource requests;
- resource limits;
- autoscaling;
- rolling deployments;
- termination grace periods;
- pod disruption;
- service discovery;
- configuration;
- secrets.

Application capacity must be evaluated across replicas.

For example:

```text
10 pods
×
4 workers
×
10 DB connections
=
400 potential DB connections
```

This can overwhelm PostgreSQL even when each individual pod appears correctly configured.

---

## AWS Considerations

Python backend applications commonly integrate with:

- ECS/EKS;
- Lambda;
- RDS PostgreSQL;
- ElastiCache Redis;
- MSK Kafka;
- S3;
- SQS;
- SNS;
- Secrets Manager;
- Parameter Store;
- CloudWatch.

AWS infrastructure does not remove application-level responsibility.

The application still needs:

- timeouts;
- retries;
- idempotency;
- connection management;
- observability;
- access control;
- graceful shutdown;
- capacity planning.

---

## High Availability

High availability is an architectural property, not merely a replica count.

A resilient Python service should consider:

```text
Multiple application replicas
        ↓
Load balancing
        ↓
Stateless application processes
        ↓
Durable PostgreSQL
        ↓
Highly available cache/message infrastructure
```

Avoid process-local state for data that must survive instance failure.

For distributed state, use appropriate durable systems such as:

- PostgreSQL;
- Redis where durability requirements permit;
- Kafka;
- S3.

---

## Reliability Principles

Several patterns recur throughout backend Python engineering.

### Timeouts

Every external dependency should have explicit time bounds.

```text
Client timeout
 ↓
Application deadline
 ↓
DB timeout
 ↓
External API timeout
```

Unbounded waits can exhaust workers and connection pools.

### Retries

Retries require:

- bounded attempts;
- exponential backoff;
- jitter;
- retryable-error classification;
- idempotency.

Retries without limits can amplify outages.

### Idempotency

Assume operations can be repeated because of:

- client retries;
- network ambiguity;
- queue redelivery;
- worker crashes;
- deployments.

### Backpressure

Bound:

- queues;
- concurrency;
- request sizes;
- batch sizes;
- connection pools.

Unbounded buffering usually moves failure into memory exhaustion or downstream overload.

---

## Disaster Recovery

Critical backend state should survive:

- process crashes;
- container replacement;
- node failure;
- deployment rollback;
- region-level incidents where applicable.

Separate:

```text
ephemeral process state
```

from:

```text
durable business state
```

For important workflows, recovery mechanisms may include:

- database transactions;
- outbox records;
- durable job state;
- Kafka retention;
- object storage;
- backups;
- replay;
- reconciliation.

---

## Cost Considerations

Performance and reliability have direct infrastructure cost.

Examples:

```text
more workers
→ more memory
→ more DB connections

larger cache
→ more Redis memory

more replicas
→ more compute
→ more connection demand

higher log volume
→ more storage and ingestion cost

more telemetry
→ higher observability cost
```

Optimize the whole system rather than one service metric.

A small latency improvement that requires significantly more infrastructure may not be economically justified.

---

## Production Engineering Workflow

When implementing a backend feature, a useful sequence is:

1. Define the API or application contract.
2. Identify authentication and authorization requirements.
3. Validate external input.
4. Define the service/use-case boundary.
5. Identify required persistence and external dependencies.
6. Define transaction boundaries.
7. Determine synchronous versus asynchronous work.
8. Define idempotency and retry behavior.
9. Add observability.
10. Define health and shutdown behavior.
11. Test failure scenarios.
12. Measure performance under realistic load.
13. Deploy with controlled rollout and rollback capability.

This encourages operational correctness before production traffic exposes missing assumptions.

---

## Common Architectural Mistakes

### Fat Controllers

Putting business logic directly in HTTP handlers makes the logic difficult to reuse and test.

Prefer:

```text
Controller
 ↓
Service
 ↓
Domain / Repository / Gateway
```

### Fat Repositories

Repositories should not become application-service replacements.

Avoid putting authorization, workflows, external API calls, and complex business orchestration into persistence classes.

### Generic Abstractions Everywhere

Abstractions should solve real coupling or ownership problems.

Do not create interfaces for every class merely to increase abstraction.

### Global Mutable State

Global state can create:

- concurrency bugs;
- test pollution;
- lifecycle problems;
- difficult deployments.

Prefer explicit dependency ownership.

### Per-Request Connection Pools

Creating database pools or HTTP clients per request defeats pooling and can exhaust resources.

Create process-scoped infrastructure where appropriate.

### Unbounded Retries

Retries without limits can turn a dependency failure into a system-wide outage.

### Missing Timeouts

An unavailable downstream service can otherwise consume workers and connections indefinitely.

### Treating Health Checks as Monitoring

Health checks answer narrow orchestration questions.

They do not replace:

- metrics;
- logs;
- traces;
- alerting.

---

## Senior-Level Design Questions

When evaluating a backend Python design, ask:

### Ownership

- Who creates this resource?
- Who closes it?
- What is its lifetime?

### Consistency

- What must be atomic?
- Where is the transaction boundary?
- What happens if the process dies after step N?

### Failure

- What happens when PostgreSQL is slow?
- What happens when Redis is unavailable?
- What happens when Kafka is unavailable?
- What happens when the external API times out?

### Retry

- Can this operation execute twice?
- Is it idempotent?
- Which failures are retryable?

### Capacity

- What is the concurrency limit?
- What downstream resource does it consume?
- How does autoscaling multiply that demand?

### Observability

- How will an engineer diagnose this failure?
- Which metric indicates the problem?
- Can the request be followed across services?

### Deployment

- What happens during rolling deployment?
- Can old and new application versions coexist?
- Can the process shut down safely?

### Recovery

- Where does durable state live?
- Can interrupted work resume?
- Can events be replayed?
- How does rollback work?

---

## Backend Python Engineering Principles

The section can be reduced to a set of practical principles:

| Principle | Engineering implication |
|---|---|
| Explicit boundaries | Keep transport, application, domain, and infrastructure responsibilities clear |
| Explicit ownership | Know who creates and closes resources |
| Short transactions | Minimize lock and connection occupancy |
| Bounded concurrency | Protect downstream dependencies |
| Explicit timeouts | Prevent indefinite resource consumption |
| Idempotent operations | Make retries and redelivery safe |
| Durable state | Do not rely on process memory for critical data |
| Observable systems | Make failures diagnosable |
| Reproducible builds | Deploy known dependency versions |
| Secure secrets | Keep credentials outside source and images |
| Graceful lifecycle | Treat startup, health, and shutdown as production behavior |
| Measure before optimizing | Use profiling, tracing, metrics, and load tests |
| Avoid unnecessary abstraction | Complexity should correspond to real system needs |

---

## Relationship to Other Playbook Sections

The Backend Python section builds on the earlier Python sections.

```text
01 Fundamentals
      ↓
02 OOP
      ↓
03 Intermediate Python
      ↓
04 Error Handling
      ↓
05 Files / Serialization
      ↓
06 Type System
      ↓
07 Data Modeling
      ↓
08 Concurrency
      ↓
09 Memory / Performance
      ↓
10 Backend Python
      ↓
11 Testing
      ↓
12 Interview Preparation
```

The boundaries are intentional.

For example:

- concurrency concepts explain worker and async behavior;
- memory concepts explain worker sizing and request memory;
- type-system concepts support repository and service interfaces;
- data modeling supports DTOs and domain models;
- error handling supports API and retry semantics;
- performance concepts support database, HTTP, and cache optimization.

---

## Recommended Engineering Mental Model

A senior Python backend engineer should think in terms of:

```text
                    ┌─────────────────┐
                    │   User Request  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Transport Layer │
                    │ HTTP / gRPC     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Security        │
                    │ Auth + AuthZ    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Validation      │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Service / Use   │
                    │ Case            │
                    └─────┬───┬───────┘
                          │   │
              ┌───────────┘   └────────────┐
              ↓                            ↓
       ┌─────────────┐              ┌─────────────┐
       │ PostgreSQL  │              │ External    │
       │ Transaction │              │ Services    │
       └──────┬──────┘              └──────┬──────┘
              │                            │
              └────────────┬───────────────┘
                           ↓
                    ┌─────────────────┐
                    │ Durable Event / │
                    │ Background Work │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Observability   │
                    │ Logs/Metrics/   │
                    │ Traces          │
                    └─────────────────┘
```

The goal is not merely to make the endpoint return the correct response.

A production backend must also behave correctly when:

- dependencies are slow;
- requests are duplicated;
- workers crash;
- messages are redelivered;
- deployments occur;
- pods terminate;
- databases fail over;
- traffic spikes;
- configuration changes;
- secrets rotate;
- external systems become unavailable.

## Key Takeaways

- **Backend Python is primarily about system boundaries:** transport, security, validation, application workflows, persistence, infrastructure, and lifecycle management should have deliberate ownership.
- **Correctness extends beyond successful requests:** transactions, idempotency, retries, durable state, message semantics, timeouts, and graceful shutdown determine how the system behaves under failure.
- **Capacity must be evaluated end-to-end:** workers, replicas, async tasks, connection pools, queues, PostgreSQL, Redis, and external APIs form one resource system.
- **Production readiness requires observability and operational design:** logs, metrics, traces, health checks, deployment behavior, security, recovery, and failure testing are part of the application.
- **Prefer explicit, measurable engineering decisions:** use abstractions where they solve real coupling problems, measure before optimizing, and design for failure rather than assuming the happy path.